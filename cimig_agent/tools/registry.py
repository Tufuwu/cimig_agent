from typing import Optional, Any, Callable, Dict
import time

from .base import Tool
from .circuit_breake import CircuitBreaker

class Registry:

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

        # 文件元数据缓存（用于乐观锁机制）
        self.read_metadata_cache: Dict[str, Dict[str, Any]] = {}

        # 熔断器（默认启用）
        self.circuit_breaker = circuit_breaker or CircuitBreaker()