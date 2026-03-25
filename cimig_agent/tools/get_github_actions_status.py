import subprocess
from pathlib import Path
from langchain_core.tools import tool
from typing import Annotated
import requests
import re

@tool
def get_github_actions_status(
    repo_path: Annotated[str, "The local filesystem path to the git repository"],
    github_token: Annotated[str, "GitHub Personal Access Token with repo/workflow scope"]
) -> str:
    """
    Checks the status and conclusion of the most recent GitHub Actions workflow run 
    for the repository linked to the local path.
    """
    path_obj = Path(repo_path).resolve()

    # 1. Retrieve the remote 'origin' URL using git CLI
    try:
        origin_url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path_obj,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return f"Error: Unable to identify a git remote origin at {repo_path}."
    except Exception as e:
        return f"Error: Git command failed: {str(e)}"

    # 2. Parse owner and repo name from the git URL
    # Supports both HTTPS and SSH formats
    match = re.search(r"(?:github\.com[:/])(.+)/([^.]+)(?:\.git)?", origin_url)
    if not match:
        return f"Error: Could not parse GitHub repository info from URL: {origin_url}"
    
    owner_raw, repo = match.group(1), match.group(2)
    # Clean up owner string (handling potential leading paths in SSH strings)
    owner = owner_raw.split('/')[-1] if '/' in owner_raw else owner_raw.split(':')[-1]

    # 3. Query the GitHub API for workflow runs
    api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        runs = data.get("workflow_runs", [])
        
        if not runs:
            return f"No workflow runs were found for {owner}/{repo}."

        # Extract info from the most recent run
        latest_run = runs[0]
        status = latest_run.get("status")
        conclusion = latest_run.get("conclusion")
        run_name = latest_run.get("display_title", "Unnamed Workflow")

        # 4. Return a descriptive string for the Agent's observation
        if status != "completed":
            return f"The latest workflow '{run_name}' is currently: {status}."
        else:
            return f"The latest workflow '{run_name}' completed with conclusion: {conclusion}."

    except requests.exceptions.RequestException as e:
        return f"Error: GitHub API request failed: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"