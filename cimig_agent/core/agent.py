from abc import ABC, abstractmethod
from typing import Optional, Iterator, List, Dict
from .message import Message
from .llm import CIMIGAgentsLLM

class Agent(ABC):
    def __init__(
            self, 
            name:str,
            llm: CIMIGAgentsLLM,
            system_prompt: Optional[str] = None,
            tool_register: Optional['ToolRegister'] = None
            
        ):
            self.name = name
            self.llm = llm
            self.system_prompt = system_prompt
            self.tool_register = tool_register

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
    
    def __str__(self) -> str:
        return f"Agent(name={self.name}, provider={self.llm.provider})"