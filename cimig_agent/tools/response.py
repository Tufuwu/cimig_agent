from dataclasses import dataclass, field
from email.mime import text
from typing import Optional, Dict, Any
from enum import Enum
import json


class ToolStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"

@dataclass
class ToolResponse:

    status: ToolStatus
    text: str
    data: Dict[str,Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, str]] = None
    stats: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status": self.status.value,
            "text": self.text,
            "data": self.data,
        }
        if self.error_info:
            result["error"] = self.error_info
        if self.stats:
            result["stats"] = self.stats
        if self.context:
            result["context"] = self.context
        return result
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str,Any]) -> 'ToolResponse':

        status_str = data.get("status", "success")
        status = ToolStatus(status_str)

        return cls(
            status=status,
            text=data.get("text", ""),
            data=data.get("data", {}),
            error_info=data.get("error"),
            stats=data.get("stats"),
            context=data.get("context")
        )
    @classmethod
    def from_json(cls, json_str: str) -> 'ToolResponse':
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def success(
        cls,
        text: str,
        data: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> 'ToolResponse':
        return cls(
            status=ToolStatus.SUCCESS,
            text=text,
            data=data or {},
            stats=stats,
            context=context
        )
    
    @classmethod
    def partial(
        cls,
        text: str,
        data: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> 'ToolResponse':
        return cls(
            status=ToolStatus.PARTIAL,
            text=text,
            data=data or {},
            stats=stats,
            context=context
        )
    
    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        stats: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> 'ToolResponse':
        return cls(
            status=ToolStatus.ERROR,
            text=message,
            data={},
            error_info={"code": code, "message": message},
            stats=stats,
            context=context
        )