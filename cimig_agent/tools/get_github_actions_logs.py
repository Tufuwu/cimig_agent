from langchain_core.tools import tool
import subprocess
from pathlib import Path
import requests
import re
import zipfile
import io
from typing import Annotated
import os

@tool
def get_github_actions_logs(
    repo_path: Annotated[str, "Local path to the git repository"]
) -> str:
    """
    Fetches the latest GitHub Actions run logs for a local Git repository.
    """
    path_obj = Path(repo_path).resolve()

    # 1. Extract remote origin URL
    try:
        origin_url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path_obj, capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return f"Error: Not a git repository or no remote origin at {repo_path}"

    # 2. Parse owner and repo name from URL
    match = re.search(r"(?:github\.com[:/])(.+)/([^.]+)(?:\.git)?", origin_url)
    if not match:
        return f"Error: Failed to parse GitHub owner/repo from {origin_url}"
    
    owner_part, repo = match.group(1), match.group(2)
    owner = owner_part.split('/')[-1] if '/' in owner_part else owner_part.split(':')[-1]

    # 3. Request GitHub API
    headers = {"Authorization": f"token {os.getenv("GITHUB_TOKEN")}", "Accept": "application/vnd.github+json"}
    runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    
    try:
        resp = requests.get(runs_url, headers=headers, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if not runs: return "No workflow runs found."

        latest_run = runs[0]
        if latest_run.get("status") != "completed":
            return f"Latest run is {latest_run.get('status')}, not completed yet."

        # 4. Download and extract logs
        logs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{latest_run['id']}/logs"
        logs_resp = requests.get(logs_url, headers=headers, timeout=20)
        
        with zipfile.ZipFile(io.BytesIO(logs_resp.content)) as z:
            logs = []
            for name in z.namelist():
                if name.endswith('.txt'):
                    with z.open(name) as f:
                        logs.append(f"FILE: {name}\n{f.read().decode('utf-8', errors='ignore')}")
        return "\n".join(logs) if logs else "No text logs found."
    except Exception as e:
        return f"API Error: {str(e)}"
