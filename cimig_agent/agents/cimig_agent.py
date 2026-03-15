from typing import Optional, Iterator, TYPE_CHECKING, List, Dict, Any, AsyncGenerator
from datetime import datetime
import json

from ..core.config import Config
from ..core import Agent
from ..core import CIMIGAgentsLLM
from ..tools.registry import ToolRegistry
from ..core.message import Message
# 新的系统提示词
DEFAULT_REACT_SYSTEM_PROMPT = """

#You are an AI assistant capable of both reasoning and taking actions.

#Workflow

##You can complete tasks by calling tools. Follow this general process:

###Thought Tool:Use this tool to record your reasoning and analysis.

-Call it whenever you need to think through a problem or plan the next step.

-Parameter: reasoning — your internal reasoning process.

##Task Tools:Use appropriate tools to retrieve information or perform actions required for the task.

You may call different tools multiple times if needed.

Finish Tool

Use this tool to return the final answer to the user.

Call it only when you are confident you have enough information to provide a complete answer.

Parameter: answer — the final response.

Important Guidelines

Proactively use the Thought tool to record your reasoning.

You may call tools multiple times to gather necessary information.

Only call Finish when you are certain that you have sufficient information to produce the final answer.
"""

class CimigAgent(Agent):

    def __init__(
            self, 
            name: str,
            llm: CIMIGAgentsLLM,
            system_prompt: str = None,
            config: Optional[Config] = None,
            tool_registry: Optional[ToolRegistry] = None,
            max_step: int = 5,
            ):
        super().__init__(
            name,
            llm,
            system_prompt or DEFAULT_REACT_SYSTEM_PROMPT,
            tool_registry=tool_registry or ToolRegistry(),
        )
        self.max_step = max_step
        self.builtin_tools = ["Thought", "Finish"]  

        from ..tools.builtin.check_workflow_result import CheckWorkResult
        from ..tools.builtin.get_wrong_log import GetWrongLog
        from ..tools.builtin.git_commit import GitCommit
        from ..tools.builtin.read_tool import ReadTool
        from ..tools.builtin.write_tool import WriteTool

        # checktools = CheckWorkResult()
        # getwronglogs = GetWrongLog()
        # gitcommit = GitCommit()
        readtool = ReadTool()
        writetool = WriteTool()

        # self.add_tool(checktools)
        # self.add_tool(getwronglogs)
        # self.add_tool(gitcommit)
        self.add_tool(readtool)
        self.add_tool(writetool)


    def add_tool(self, tool):
        self.tool_registry.register_tool(tool)

    def run(self, input_text: str, **kwargs) -> str:

        session_start_time = datetime.now()
        try:
            # 执行主逻辑
            final_answer = self._run_impl(input_text, session_start_time, **kwargs)

            # 更新元数据
            self._session_metadata["total_steps"] = getattr(self, '_current_step', 0)
            self._session_metadata["total_tokens"] = getattr(self, '_total_tokens', 0)

            return final_answer

        except KeyboardInterrupt:
            # Ctrl+C 时自动保存
            print("\n 用户中断，自动保存会话...")
            if self.session_store:
                try:
                    filepath = self.save_session("session-interrupted")
                    print(f"会话已保存: {filepath}")
                except Exception as e:
                    print(f"保存失败: {e}")
            raise

        except Exception as e:
            # 错误时也尝试保存
            print(f"\n 发生错误: {e}")
            if self.session_store:
                try:
                    filepath = self.save_session("session-error")
                    print(f"会话已保存: {filepath}")
                except Exception as save_error:
                    print(f"保存失败: {save_error}")
            raise

    def _run_impl(self,input_text: str, session_start_time, **kwargs) -> str:
        messages = self._build_messages(input_text)
        tool_schemas = self._build_tool_schemas()

        current_step = 0
        total_tokens = 0

        if self.trace_logger:
            self.trace_logger.log_event(
                "message_written",
                {"role": "user", "content": input_text}
            )
        
        print(f"{self.name}开始处理问题:{input_text}")

        while current_step < self.max_step:
            current_step += 1
            print(f"\n--- 第{current_step}step---")

            self.current_step = current_step

            try:
                response = self.llm.invoke_with_tools(
                    messages=messages,
                    tools=tool_schemas,
                    tool_choice="auto",
                    **kwargs
                )
            except Exception as e:
                print(f"LLM调用失败: {e}")
                if self.trace_logger:
                    self.trace_logger.log_event(
                        "error",
                        {"error_type": "llm_call_failed", "message": str(e)},
                        step=current_step
                    )
                break

            response_message = response.choices[0].message

            if response.usage:
                total_tokens += response.usage.total_tokens
                self.total_tokens = total_tokens
            
            if self.trace_logger:
                self.trace_logger.log_event(
                    "model_output",
                    {
                        "content": response_message.content or "",
                        "tool_calls": len(response_message.tool_calls) if response_message.tool_calls else 0,
                        "usage": {
                            "total_tokens": response.usage.total_tokens if response.usage else 0,
                            "cost": 0.0
                        }
                    },
                    step=current_step
                )
            # 处理工具调用
            tool_calls = response_message.tool_calls
            if not tool_calls:
                # 没有工具调用，直接返回文本响应
                final_answer = response_message.content or "抱歉，我无法回答这个问题。"
                print(f"直接回复: {final_answer}")

                # 保存到历史记录
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))

                if self.trace_logger:
                    duration = (datetime.now() - session_start_time).total_seconds()
                    self.trace_logger.log_event(
                        "session_end",
                        {
                            "duration": duration,
                            "total_steps": current_step,
                            "final_answer": final_answer,
                            "status": "success"
                        }
                    )
                    self.trace_logger.finalize()

                return final_answer

            # 将助手消息添加到历史
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            # 执行所有工具调用
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    print(f"❌ 工具参数解析失败: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"错误：参数格式不正确 - {str(e)}"
                    })
                    continue

                # 记录工具调用
                if self.trace_logger:
                    self.trace_logger.log_event(
                        "tool_call",
                        {
                            "tool_name": tool_name,
                            "tool_call_id": tool_call_id,
                            "args": arguments
                        },
                        step=current_step
                    )

                # 检查是否是内置工具
                if tool_name in self._builtin_tools:
                    result = self._handle_builtin_tool(tool_name, arguments)
                    print(f"🔧 {tool_name}: {result['content']}")

                    # 记录工具结果
                    if self.trace_logger:
                        self.trace_logger.log_event(
                            "tool_result",
                            {
                                "tool_name": tool_name,
                                "tool_call_id": tool_call_id,
                                "status": "success",
                                "result": result['content']
                            },
                            step=current_step
                        )

                    # 检查是否是 Finish
                    if tool_name == "Finish" and result.get("finished"):
                        final_answer = result["final_answer"]
                        print(f"🎉 最终答案: {final_answer}")

                        # 保存到历史记录
                        self.add_message(Message(input_text, "user"))
                        self.add_message(Message(final_answer, "assistant"))

                        if self.trace_logger:
                            duration = (datetime.now() - session_start_time).total_seconds()
                            self.trace_logger.log_event(
                                "session_end",
                                {
                                    "duration": duration,
                                    "total_steps": current_step,
                                    "final_answer": final_answer,
                                    "status": "success"
                                }
                            )
                            self.trace_logger.finalize()

                        return final_answer

                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result['content']
                    })
                else:
                    # 用户工具
                    print(f"🎬 调用工具: {tool_name}({arguments})")

                    # 执行工具（使用基类方法，支持字典参数）
                    result = self._execute_tool_call(tool_name, arguments)

                    # 记录工具结果
                    if self.trace_logger:
                        self.trace_logger.log_event(
                            "tool_result",
                            {
                                "tool_name": tool_name,
                                "tool_call_id": tool_call_id,
                                "result": result
                            },
                            step=current_step
                        )

                    # 检查是否是错误
                    if result.startswith("❌"):
                        print(result)
                    else:
                        print(f"👀 观察: {result}")

                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result
                    })

        # 达到最大步数
        print("⏰ 已达到最大步数，流程终止。")
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))

        # 记录会话结束（超时）
        if self.trace_logger:
            duration = (datetime.now() - session_start_time).total_seconds()
            self.trace_logger.log_event(
                "session_end",
                {
                    "duration": duration,
                    "total_steps": current_step,
                    "final_answer": final_answer,
                    "status": "timeout"
                }
            )
            self.trace_logger.finalize()

        return final_answer
    
    def _build_messages(self, input_text: str) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []

        # 添加系统提示词
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # 添加用户问题
        messages.append({
            "role": "user",
            "content": input_text
        })

        return messages
    
    
    def _build_tool_schemas(self) -> List[Dict[str, Any]]:
        """构建工具 JSON Schema(包含内置工具和用户工具)

        复用基类的 _build_tool_schemas()，并追加 ReAct 内置工具
        """
        schemas = []

        # 1. 添加内置工具：Thought
        schemas.append({
            "type": "function",
            "function": {
                "name": "Thought",
                "description": "分析问题，制定策略，记录推理过程。在需要思考时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "你的推理过程和分析"
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        })

        # 2. 添加内置工具：Finish
        schemas.append({
            "type": "function",
            "function": {
                "name": "Finish",
                "description": "当你有足够信息得出结论时，使用此工具返回最终答案。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                       "type": "string",
                            "description": "最终答案"
                        }
                    },
                    "required": ["answer"]
                }
            }
        })


        # 3. 添加用户工具（复用基类方法）
        if self.tool_registry:
            user_tool_schemas = super()._build_tool_schemas()
            schemas.extend(user_tool_schemas)

        return schemas