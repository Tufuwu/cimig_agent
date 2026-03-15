import os
from typing import Optional, Iterator, List, Dict, Union, Any, AsyncIterator

from .exceptions import CIMIGAgentsException
from .llm_response import LLMResponse, StreamStats
from .llm_adapters import create_adapter, BaseLLMAdapter



class CIMIGAgentsLLM:
    """
    CIMIGAgents base client

    Design Principles:
    - 统一配置：只需 LLM_MODEL_ID、LLM_API_KEY、LLM_BASE_URL、LLM_TIMEOUT
    - 自动适配:根据base_url自动选择适配器(OpenAI/Anthropic/Gemini)
    - 统计信息:返回token使用量、耗时等信息,方便日志记录
    - Thinking Model:自动识别并处理推理过程(o1、deepseek-reasoner等)

    支持的接口：
    - OpenAI及所有兼容接口(DeepSeek、Qwen、Kimi、智谱、Ollama等)
    - Anthropic Claude
    - Google Gemini
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        """
        初始化LLM客户端

        参数优先级：传入参数 > 环境变量

        Args:
            model: 模型名称,默认从 LLM_MODEL_ID 读取
            api_key: API密钥,默认从 LLM_API_KEY 读取
            base_url: 服务地址,默认从 LLM_BASE_URL 读取
            temperature: 温度参数,默认0.7
            max_tokens: 最大token数
            timeout: 超时时间（秒）,默认从 LLM_TIMEOUT 读取,默认60秒
        """
        # 加载配置
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        # 2. 检查 model
        if not self.model:
            raise CIMIGAgentsException(
                "必须提供模型名称(model参数或LLM_MODEL_ID环境变量)"
            )

        # 3. 自动检测 provider
        self.provider = self._auto_detect_provider(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 4. 根据 provider 解析 credentials
        self.api_key, self.base_url = self._resolve_credentials(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 5. 最终校验
        if not self.api_key:
            raise CIMIGAgentsException(
                "必须提供API密钥(api_key参数或LLM_API_KEY环境变量)"
            )

        if not self.base_url:
            raise CIMIGAgentsException(
                "必须提供服务地址(base_url参数或LLM_BASE_URL环境变量)"
            )

        
        # 创建适配器（自动检测）
        self._adapter: BaseLLMAdapter = create_adapter(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            model=self.model
        )

        # 最后一次调用的统计信息（用于流式调用）
        self.last_call_stats: Optional[StreamStats] = None

    def _auto_detect_provider(self, api_key: Optional[str], base_url: Optional[str]) -> str:
        """
        自动检测LLM提供商
        """
        # 1. 检查特定提供商的环境变量 (最高优先级)
        if os.getenv("MODELSCOPE_API_KEY"): return "modelscope"
        if os.getenv("OPENAI_API_KEY"): return "openai"
        if os.getenv("ZHIPU_API_KEY"): return "zhipu"
        # ... 其他服务商的环境变量检查

        # 获取通用的环境变量
        actual_api_key = api_key or os.getenv("LLM_API_KEY")
        actual_base_url = base_url or os.getenv("LLM_BASE_URL")

        # 2. 根据 base_url 判断
        if actual_base_url:
            base_url_lower = actual_base_url.lower()
            if "api-inference.modelscope.cn" in base_url_lower: return "modelscope"
            if "open.bigmodel.cn" in base_url_lower: return "zhipu"
            if "localhost" in base_url_lower or "127.0.0.1" in base_url_lower:
                if ":11434" in base_url_lower: return "ollama"
                if ":8000" in base_url_lower: return "vllm"
                return "local" # 其他本地端口

        # 3. 根据 API 密钥格式辅助判断
        if actual_api_key:
            if actual_api_key.startswith("ms-"): return "modelscope"
            # ... 其他密钥格式判断

        # 4. 默认返回 'auto'，使用通用配置
        return "auto"
    
    def _resolve_credentials(self, api_key: Optional[str], base_url: Optional[str]) -> tuple[str, str]:
        """根据provider解析API密钥和base_url"""
        if self.provider == "openai":
            resolved_api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
            resolved_base_url = base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
            return resolved_api_key, resolved_base_url

        elif self.provider == "modelscope":
            resolved_api_key = api_key or os.getenv("MODELSCOPE_API_KEY") or os.getenv("LLM_API_KEY")
            resolved_base_url = base_url or os.getenv("LLM_BASE_URL") or "https://api-inference.modelscope.cn/v1/"
            return resolved_api_key, resolved_base_url
    
    # ... 其他服务商的逻辑
    def think(self, messages: List[Dict], temperature: Optional[float] = None) -> Iterator[str]:
        """
        args:
           messages
           temperature
        """
        print(f"正在调用模型 {self.model} ...")

        # prepare kwargs
        kwargs = {
            "temperature": temperature if temperature is not None else self.temperature
        }
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        
        try:
            print(f"大语言模型响应成功:")
            for chunk in self._adapter.stream_invoke(messages, **kwargs):
                print(chunk, end="", flush=True)
                yield chunk
            print()  # 换行

            if hasattr(self._adapter, 'last_stats'):
                self.last_call_stats = self._adapter.last_stats

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            raise CIMIGAgentsException(f"调用LLM API失败: {str(e)}")
        

    def invoke_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        tool_choice: Union[str, Dict] = "auto",
        **kwargs
    ) -> Any:
        
        call_kwargs = {
            "temperature": kwargs.get("temperature", self.temperature)
      
        }
        if self.max_tokens is not None:
            call_kwargs["max_tokens"] = self.max_tokens
        call_kwargs.update(kwargs)

        return self._adapter.invoke_with_tools(messages=messages, tools=tools, **call_kwargs)
    