import subprocess
from pathlib import Path

from ..base import Tool, ToolParameters

class GitCommit(Tool):
    def __init__(self):
        super().__init__(
            name="git_commit_tool",
            description="Commit and push changes to a local Git repository. "
        )

    def run(self, commit_message: str, repo_path: str = "."):
        """
        Commit and push changes to the specified local Git repository.
        """
        repo_path = Path(repo_path).resolve()  # Ensure absolute path

        # Get origin URL
        origin_url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        print(f"Pushing to repository: {origin_url}")

        # Stage all changes
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)

        # Check if there are changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if status.stdout.strip() == "":
            return "No changes detected. Skipping commit and push."

        # Commit changes
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True)
        print(f"Changes committed with message: {commit_message}")

        # Push to origin/main
        subprocess.run(["git", "push", "origin", "main"], cwd=repo_path, check=True)
        return f"Changes committed and pushed to {origin_url}."

    def get_parameters(self):
        """
        Return the parameters required by the tool, for agent usage.
        """
        return {
            "commit_message": {
                "type": "string",
                "description": "The commit message for the changes."
            },
            "repo_path": {
                "type": "string",
                "description": "Path to the local Git repository. Default is current directory.",
                "optional": True
            }
        }