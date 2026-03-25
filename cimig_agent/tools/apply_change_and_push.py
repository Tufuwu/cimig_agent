import subprocess
from pathlib import Path
from typing import Annotated
from langchain_core.tools import tool

@tool
def apply_change_and_push(
    file_path: Annotated[str, "The target local path to save the file"],
    content: Annotated[str, "The string content to write into the file"],
    commit_message: Annotated[str, "The descriptive message for the git commit"],
    repo_path: Annotated[str, "The local filesystem path to the git repository (usually the root)"] = "."
) -> str:
    """
    A compound tool that writes content to a file, stages it, and pushes the change to GitHub.
    Use this to apply fixes and trigger CI/CD builds in one single action.
    """
    path_obj = Path(repo_path).resolve()
    target_file = Path(file_path).resolve()

    try:
        # 1. Write the file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
        
        # 2. Check for changes in the git repo
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path_obj, capture_output=True, text=True, check=True
        )
        
        if not status.stdout.strip():
            return f"Success: File {file_path} written, but no git changes detected (content might be identical)."

        # 3. Git Add, Commit, and Push
        subprocess.run(["git", "add", "."], cwd=path_obj, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=path_obj, check=True)
        
        # Attempt to push to origin main
        process_push = subprocess.run(
            ["git", "push", "origin", "main"], 
            cwd=path_obj, capture_output=True, text=True
        )

        if process_push.returncode != 0:
            return f"File saved and committed, but PUSH FAILED: {process_push.stderr}"

        return f"Success: File {file_path} applied and pushed to remote with message: '{commit_message}'."

    except Exception as e:
        return f"Error during combined operation: {str(e)}"
