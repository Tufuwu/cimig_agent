from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.message import Message


class HistoryManager:

    def __init__(
        self,
        min_retain_rounds: int = 10,
        compression_threshold: float = 0.8
    ):
        """初始化历史管理器
        
        Args:
            min_retain_rounds: 压缩时保留的最小完整轮次数
            compression_threshold: 压缩阈值（暂未使用，预留）
        """
        self._history: List[Message] = []
        self.min_retain_rounds = min_retain_rounds
        self.compression_threshold = compression_threshold

    def get_history(self) -> List[Message]:
        """获取历史副本
        
        Returns:
            历史消息列表的副本
        """
        return self._history.copy()