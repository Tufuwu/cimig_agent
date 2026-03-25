from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Iterator, List, Dict, Any,TYPE_CHECKING

from .message import Message
from .llm import CIMIGAgentsLLM
from .config import Config
from ..observability.trace_logger import TraceLogger
from .session_store import SessionStore
if TYPE_CHECKING:
    from ..tools.registry import ToolRegistry

class Agent(ABC):
    def __init__(
        self,
        name: str,
        llm: CIMIGAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional["ToolRegistry"] = None
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self.tool_registry = tool_registry
        self.session_store: Optional[SessionStore] = None
        self.trace_logger: Optional[TraceLogger] = None
        from ..context.history import HistoryManager

        self.history_manager = HistoryManager(
            min_retain_rounds=self.config.min_retain_rounds,
            compression_threshold=self.config.compression_threshold
        )

        if self.config.session_enabled:
            self.session_store = SessionStore(session_dir=self.config.session_dir)
        self._session_metadata = {
            "created_at": datetime.now().isoformat(),
            "total_tokens": 0,
            "total_steps": 0,
            "duration_seconds": 0
        }
        self._start_time = datetime.now()

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行Agent"""
        pass
    
    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self._history.append(message)
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()
    
    def get_history(self) -> list[Message]:
        """获取历史记录"""
        return self._history.copy()
    
    @property
    def _history(self) -> List[Message]:
        """向后兼容：通过 property 代理到 HistoryManager"""
        return self.history_manager.get_history()

    @_history.setter
    def _history(self, value: List[Message]):
        """向后兼容：允许直接设置历史"""
        self.history_manager.clear()
        for msg in value:
            self.history_manager.append(msg)
    
    def __str__(self) -> str:
        return f"Agent(name={self.name}, provider={self.llm.provider})"
    
    def _build_tool_schemas(self) -> List[Dict[str, Any]]:
        """构建工具 JSON Schema

        统一的工具 schema 构建逻辑，支持：
        - Tool 对象（带参数定义）
        - 函数工具（简化注册）

        Returns:
            工具 schema 列表
        """
        if not self.tool_registry:
            return []

        schemas: List[Dict[str, Any]] = []

        # 1. 处理 Tool 对象
        for tool in self.tool_registry.get_all_tools():
            properties: Dict[str, Any] = {}
            required: List[str] = []

            try:
                parameters = tool.get_parameters()
            except Exception:
                parameters = []

            for param in parameters:
                properties[param.name] = {
                    "type": self._map_parameter_type(param.type),
                    "description": param.description or ""
                }
                if param.default is not None:
                    properties[param.name]["default"] = param.default
                if getattr(param, "required", True):
                    required.append(param.name)

            schema: Dict[str, Any] = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties
                    }
                }
            }
            if required:
                schema["function"]["parameters"]["required"] = required
            schemas.append(schema)

        # 2. 处理函数工具
        function_map = getattr(self.tool_registry, "_functions", {})
        for name, info in function_map.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "输入文本"
                            }
                        },
                        "required": ["input"]
                    }
                }
            })

        return schemas
    @staticmethod
    def _map_parameter_type(param_type: str) -> str:
        """将工具参数类型映射为 JSON Schema 允许的类型

        Args:
            param_type: 工具参数类型

        Returns:
            JSON Schema 类型
        """
        normalized = (param_type or "").lower()
        if normalized in {"string", "number", "integer", "boolean", "array", "object"}:
            return normalized
        return "string"

    def _convert_parameter_types(self, tool_name: str, param_dict: Dict[str, Any]) -> Dict[str, Any]:
        """根据工具定义转换参数类型

        Args:
            tool_name: 工具名称
            param_dict: 参数字典

        Returns:
            类型转换后的参数字典
        """
        if not self.tool_registry:
            return param_dict

        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return param_dict

        try:
            tool_params = tool.get_parameters()
        except Exception:
            return param_dict

        type_mapping = {param.name: param.type for param in tool_params}
        converted: Dict[str, Any] = {}

        for key, value in param_dict.items():
            param_type = type_mapping.get(key)
            if not param_type:
                converted[key] = value
                continue

            try:
                normalized = param_type.lower()
                if normalized in {"number", "float"}:
                    converted[key] = float(value)
                elif normalized in {"integer", "int"}:
                    converted[key] = int(value)
                elif normalized in {"boolean", "bool"}:
                    if isinstance(value, bool):
                        converted[key] = value
                    elif isinstance(value, (int, float)):
                        converted[key] = bool(value)
                    elif isinstance(value, str):
                        converted[key] = value.lower() in {"true", "1", "yes"}
                    else:
                        converted[key] = bool(value)
                else:
                    converted[key] = value
            except (TypeError, ValueError):
                converted[key] = value

        return converted

    def _execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        执行工具调用并返回字符串结果

        统一的工具执行逻辑，支持：
        - Tool 对象（带类型转换）
        - 函数工具（简化调用）

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果（字符串格式）
        """
        if not self.tool_registry:
            return "❌ 错误：未配置工具注册表"

        # 1. 尝试执行 Tool 对象
        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            try:
                typed_arguments = self._convert_parameter_types(tool_name, arguments)
                response = tool.run_with_timing(typed_arguments)

                # 根据状态添加前缀
                from ..tools.response import ToolStatus
                if response.status == ToolStatus.ERROR:
                    error_code = response.error_info.get("code", "UNKNOWN") if response.error_info else "UNKNOWN"
                    return f"❌ 错误 [{error_code}]: {response.text}"
                elif response.status == ToolStatus.PARTIAL:
                    return f"⚠️ 部分成功: {response.text}"
                else:
                    return response.text
            except Exception as exc:
                return f"❌ 工具调用失败：{exc}"

        # 2. 尝试执行函数工具
        func = self.tool_registry.get_function(tool_name)
        if func:
            try:
                input_text = arguments.get("input", "")
                response = self.tool_registry.execute_tool(tool_name, input_text)

                # 根据状态添加前缀
                from ..tools.response import ToolStatus
                if response.status == ToolStatus.ERROR:
                    error_code = response.error_info.get("code", "UNKNOWN") if response.error_info else "UNKNOWN"
                    return f"❌ 错误 [{error_code}]: {response.text}"
                elif response.status == ToolStatus.PARTIAL:
                    return f"⚠️ 部分成功: {response.text}"
                else:
                    return response.text
            except Exception as exc:
                return f"❌ 工具调用失败：{exc}"

        return f"❌ 错误：未找到工具 '{tool_name}'"