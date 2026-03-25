from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from .state import State  # 导入定义的 State
from ..tools.get_github_actions_status import get_github_actions_status
from ..tools.get_github_actions_logs import get_github_actions_logs
from ..tools.apply_change_and_push import apply_change_and_push
from ..tools.read_file import read_file

# collect all the tools
tools = [apply_change_and_push, get_github_actions_logs, get_github_actions_status,read_file]

# 定义模型并绑定工具
model = ChatOpenAI(model="gpt-4o").bind_tools(tools)

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState  # 导入你的 State

# --- 1. 节点逻辑 (执行者) ---
def call_model(state: AgentState):
    response = model.invoke(state["messages"])
    # 每次经过 Agent，计数器 +1
    return {
        "messages": [response],
        "loop_count": state.get("loop_count", 0) + 1
    }

# --- 2. 路由逻辑 (决策者：写在 Graph 逻辑内) ---
def should_continue(state: AgentState):
    # 1. 强制终止逻辑 (Safety Break)
    # 如果节点执行次数过多（例如超过 20 次节点激活），强行停止
    if state.get("loop_count", 0) > 20:
        return "end"

    last_message = state["messages"][-1]
    
    # 2. ReAct 核心判定
    # 如果模型产生了 tool_calls，说明它进入了 'Action' 阶段
    if last_message.tool_calls:
        return "tools"
    
    # 3. 否则进入 'Final Answer' 阶段
    return "end"

# --- 3. 构建图 ---
def create_agent_app():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("agent")
    
    # 关键：将逻辑函数绑定到 agent 节点之后
    workflow.add_conditional_edges(
        "agent", 
        should_continue,
        {
            "tools": "tools",  # 返回 "tools" 时跳转到 tools 节点
            END: END           # 返回 END 时结束
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()