from typing import Optional, Dict
from dataclasses import dataclass, field

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    reasoning_content: Optional[str] = None


@dataclass
class StreamStats:

    model: str

    usage: Dict[str, int] = field(default_factory=dict)

    resoning_content: Optional[str] = None