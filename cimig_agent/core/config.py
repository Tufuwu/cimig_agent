import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

class Config(BaseModel):

    default_model: str = "gpt-4o-mini"
    default_provider: str = "openai"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    debug: bool = False
    log_level: str = "INFO"

    min_retain_rounds: int = 10 
    compression_threshold: float = 0.8
    
    session_enabled: bool = True  # 是否启用会话持久化
    session_dir: str = "memory/sessions"  # 会话文件保存目录
    max_history_length: int = 100

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "0")) or None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()