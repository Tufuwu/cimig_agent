from typing import Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage
from operator import add

class AgentState(TypedDict):
    # 1. 对话历史 (必须)
    messages: Annotated[list[BaseMessage], add]
    
    # 2. 迭代计数器 (用于控制 3 次纠错循环)
    loop_count: int
    
