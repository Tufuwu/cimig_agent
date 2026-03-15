import json
import uuid 
from pathlib import Path
from datetime import datetime

class SessionStore:

    def __init__(self, session_dir: str = "memory/sessions"):
        """初始化会话存储器
        
        Args:
            session_dir: 会话文件保存目录
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _generate_session_id(self) -> str:
        """生成唯一的会话 ID
        
        格式：s-{timestamp}-{uuid}
        
        Returns:
            会话 ID
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_suffix = uuid.uuid4().hex[:8]
        return f"s-{timestamp}-{unique_suffix}"