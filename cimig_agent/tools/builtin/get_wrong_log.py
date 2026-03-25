from langchain.tools import Tool
import subprocess
from pathlib import Path
import requests
import re
import zipfile
import io

class GitHubActionsLogs(Tool):
    def __init__(self, github_token: str):
        """
        Tool to fetch the latest GitHub Actions run logs for a local repository.

        Args:
            github_token (str): Personal Access Token with repo/workflow permissions
        """
        self.github_token = github_token
        super().__init__(
            name="github_actions_logs",
            description="Get the latest GitHub Actions run logs for a local Git repository. "
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

        # 3️⃣ Get latest workflow run
        runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        response = requests.get(runs_url, headers=headers)
        if response.status_code != 200:
            return f"Error: GitHub API request failed with status {response.status_code}"

        data = response.json()
        runs = data.get("workflow_runs")
        if not runs:
            return f"No workflow runs found for repository {owner}/{repo}"

        latest_run = runs[0]
        run_id = latest_run.get("id")
        status = latest_run.get("status")
        conclusion = latest_run.get("conclusion")

        # 4️⃣ If the latest run is not completed
        if status != "completed":
            return f"Latest run is not completed yet. Current status: {status}"

        # 5️⃣ Download logs for the latest run
        logs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        logs_response = requests.get(logs_url, headers=headers, stream=True)
        if logs_response.status_code != 200:
            return f"Error: Failed to download logs, status {logs_response.status_code}"

        # Logs are returned as a zip file
        with zipfile.ZipFile(io.BytesIO(logs_response.content)) as z:
            all_logs = []
            for filename in z.namelist():
                with z.open(filename) as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    all_logs.append(f"=== {filename} ===\n{content}\n")
        
        return "\n".join(all_logs)

    def get_parameters(self):
        return {
            "repo_path": {
                "type": "string",
                "description": "Path to the local Git repository."
            }
        }