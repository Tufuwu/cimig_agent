import time
from abc import ABC, abstractmethod
from typing import Optional, Iterator, List, Dict, Any, Union, AsyncIterator
from xmlrpc import client
from xmlrpc import client

from .llm_response import LLMResponse, StreamStats
from .exceptions import CIMIGAgentsException

class BaseLLMAdapter(ABC):

    def __init__(self, api_key: str, base_url: Optional[str], timeout: int, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.model = model
        self._client = None
        self._async_client = None


    @abstractmethod
    def create_client(self) -> Any:
        """创建客户端实例"""
        pass

    @abstractmethod
    def invoke(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """非流式调用"""
        pass

    @abstractmethod
    def stream_invoke(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """流式调用，返回生成器"""
        pass

    @abstractmethod
    def invoke_with_tools(self, messages: List[Dict], tools: List[Dict], **kwargs) -> Any:
        """工具调用（Function Calling）"""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """create openai client"""
    def create_client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def invoke(self, messages: List[Dict], **kwargs) -> LLMResponse:
        
        if not self._client:
            self._client = self.create_client()

        start_time = time.time()
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )

            latency_ms = int((time.time() - start_time) * 1000)

            choice = response.choices[0]
            content = choice.message.content or ""
            reasoning_content = None

            if hasattr(choice.message, 'reasoning_content'):
                reasoning_content = choice.message.reasoning_content

            elif hasattr(choice, 'reasoning_content'):
                reasoning_content = choice.reasoning_content
            usage = {}
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            return LLMResponse(
                text=choice.content,
                model=self.model,
                usage=usage,
                latency_ms=latency_ms,
                reasoning_content=reasoning_content
            )
        except Exception as e:
            raise CIMIGAgentsException(f"openai api failed: {str(e)}")


    def stream_invoke(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        if not self._client:
            self._client = self.create_client()

        start_time = time.time()
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **kwargs
            )

            collected_content = []
            reasoning_content = None
            usage = {}

            for chunk in response:
                if 'choices' in chunk and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if 'content' in delta:
                        collected_content.append(delta.content)
                        yield delta.content
                    
                    if self._is_thinking_model(self.model):
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            if reasoning_content is None:
                                reasoning_content = ""
                            reasoning_content += delta.reasoning_content
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens
                    }
            latency_ms = int((time.time() - start_time) * 1000)

            self.last_stats = StreamStats(
                model=self.model,
                usage=usage,
                latency_ms=latency_ms,
                resoning_content=reasoning_content
            )

        except Exception as e:
            raise CIMIGAgentsException(f"openai api failed: {str(e)}")
        
    def invoke_with_tools(self, messages: List[Dict], tools: List[Dict],
                         tool_choice: Union[str, Dict] = "auto", **kwargs) -> Any:
        if not self._client:
            self._client = self.create_client()
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                **kwargs
            )
            return response
        
        except Exception as e:
            raise CIMIGAgentsException(f"openai tool call failed: {str(e)}")

def create_adapter(
    api_key: str,
    base_url: Optional[str],
    timeout: int,
    model: str
) -> BaseLLMAdapter:
    """
    根据base_url自动选择适配器

    检测逻辑：
    - anthropic.com -> AnthropicAdapter
    - googleapis.com 或 generativelanguage -> GeminiAdapter
    - 其他 -> OpenAIAdapter(默认)
    """
    # if base_url:
    #     base_url_lower = base_url.lower()

    #     if "anthropic.com" in base_url_lower:
    #         return AnthropicAdapter(api_key, base_url, timeout, model)

    #     if "googleapis.com" in base_url_lower or "generativelanguage" in base_url_lower:
    #         return GeminiAdapter(api_key, base_url, timeout, model)

    # 默认使用OpenAI适配器（兼容所有OpenAI格式接口）
    return OpenAIAdapter(api_key, base_url, timeout, model)