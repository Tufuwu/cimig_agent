from ..base import Tool, ToolParameters
class CheckWorkResult(Tool):
    def __init__(self):
        super().__init__(
            name="git_commit_tool",
            description="Read file from target path"
        )

    def run(self):
        pass

    def get_parameters(self):
        pass