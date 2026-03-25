from langchain.tools import Tool
import subprocess
from pathlib import Path
import requests
import re



class GitHubActionsStatus(Tool):
    def __init__(self, github_token: str):
        """
        Tool to fetch the latest GitHub Actions run status for a local repository.

        Args:
            github_token (str): Personal Access Token with repo/workflow permissions
        """
        self.github_token = github_token
        super().__init__(
            name="github_actions_status",
            description="Get the latest GitHub Actions run status for a local Git repository. "
                        "Parameters: repo_path (str) - local repository path"
        )

    def run(self, repo_path: str):
        repo_path = Path(repo_path).resolve()

        # 1️⃣ Get remote URL
        try:
            origin_url = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            return f"Error: Unable to get remote URL from {repo_path}"

        # 2️⃣ Parse owner and repo
        match = re.search(r"(?:github\.com[:/])(.+)/([^.]+)(?:\.git)?", origin_url)
        if not match:
            return f"Error: Cannot parse owner/repo from URL: {origin_url}"
        owner, repo = match.group(1), match.group(2)

        # 3️⃣ Call GitHub API
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error: GitHub API request failed with status {response.status_code}"

        data = response.json()
        runs = data.get("workflow_runs")
        if not runs:
            return f"No workflow runs found for repository {owner}/{repo}"

        latest_run = runs[0]

        # 4️⃣ Determine status
        status = latest_run.get("status")
        conclusion = latest_run.get("conclusion")

        if status != "completed":
            return f"Latest run is not completed yet. Current status: {status}"
        else:
            return f"Latest run completed with conclusion: {conclusion}"

    def get_parameters(self):
        return {
            "repo_path": {
                "type": "string",
                "description": "Path to the local Git repository."
            }
        }