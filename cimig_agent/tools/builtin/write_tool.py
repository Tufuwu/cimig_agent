from pathlib import Path
from typing import Dict, Any, List

from ..base import Tool, ToolParameters
from ..response import ToolResponse

class WriteTool(Tool):
    
    def __init__(self):
        super().__init__(
            name="write_tool",
            description="write file in target path"
        )
    def run(self, parameter: Dict[str, Any]) -> ToolResponse:
        """
        save file
        parameters:
            file_path: save path
            content: the content to save
        return:
            ToolResponse
        """
        file_path = parameter.get("file_path","")
        content = parameter.get("content","")

        if not file_path:
            return
        
        if not content:
            return
        
        print(f"try to save {file_path}")

        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, mode='w', encoding='utf-8',errors='ignore') as file:
                file.write(content)
                print(f'已将内容写入到 {file_path}')
            return ToolResponse.success(
                text=f"save result:success"
            )
        except:
            pass

        
    def get_parameters(self):
        from ..base import ToolParameters
        return [
            ToolParameters(
                name="file_path",
                type="string",
                description="the path of file",
                required=True
            ),
            ToolParameters(
                name="content",
                type="string",
                description="the content to save",
                required=True
            )
        ]