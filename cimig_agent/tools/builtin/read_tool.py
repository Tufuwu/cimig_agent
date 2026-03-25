from pathlib import Path
from typing import Dict, Any, List

from ..base import Tool, ToolParameters
from ..response import ToolResponse
from ..errors import ToolErrorCode

class ReadTool(Tool):
    def __init__(self):
        super().__init__(
            name="read_tool",
            description="Read file from target path"
        )
    def run(self, parameter: Dict[str, Any]) -> ToolResponse:
        """
        read file
        parameters:
            file_path: file path
        return:
            ToolResponse
        """
        file_path = parameter.get("file_path","")
        print(file_path)
        if not file_path:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_PARAM,
                message="path can not empty"
            )

        
        print(f"try to read {file_path}")

        try:
            file_path = Path(file_path)
            if not Path(file_path).exists():
                return
            with open(file_path, mode='r', encoding='utf-8',errors='ignore') as file:
                content = file.read()
                print(f'read content from {file_path}')

            return ToolResponse.success(
                text=f"read result:success",
            data={
                "file_path": file_path,
                "content": content,
                "result_type": "str",
            }
            )
        except Exception as e:
            error_msg = f"read failed: {str(e)}"
            print(f"❌ {error_msg}")
            return ToolResponse.error(
                code=ToolErrorCode.EXECUTION_ERROR,
                message=error_msg,
                context={"expression": file_path}
            )
        
    def get_parameters(self):
        return [
            ToolParameters(
                name="file_path",
                type="string",
                description="the path of file",
                required=True
            )
        ]