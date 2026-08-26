import os
import requests
from dotenv import load_dotenv

load_dotenv()
DEFAULT_TOKEN = os.getenv("GITHUB_TOKEN")


def _headers(token: str | None = None)-> dict :
    return {
    "Authorization": f"Bearer {token or DEFAULT_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_pr_diff(owner: str, repo: str, pr_number: int, token: str | None = None ) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=_headers(token))
    response.raise_for_status()  # crashes 

    files = response.json()
    full_diff = ""
    for file in files:
        if "patch" in file:  # some files (e.g. binary) have no patch
            full_diff += f"\n--- {file['filename']} ---\n{file['patch']}\n"
    return full_diff


def post_pr_comment(owner: str, repo: str, pr_number: int, comment: str,token:str | None = None):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    response = requests.post(url, headers=_headers(token), json={"body": comment})
    response.raise_for_status()
    return response.json()