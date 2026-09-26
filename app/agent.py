# app/agent.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Literal
from pydantic import BaseModel


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# for eval, force beta module to load now,on main thread
_ = client.beta.chat.completions

class Issue(BaseModel):
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    category: Literal["security", "style", "logic"]
    line: int
    message: str

class IssueList(BaseModel):
    issues: List[Issue]

# Aim for ~3,500 tokens max per chunk
MAX_DIFF_CHUNK = 14000 

def chunk_files(files: List[dict], max_size: int = MAX_DIFF_CHUNK) -> List[str]:
    chunks = []
    current_chunk = ""

    for file in files:
        filename = file.get("filename", "unknown")
        patch = file.get("patch", "")
        if not patch:
            continue

        file_diff = f"\n--- {filename} ---\n{patch}\n"

        # If a single file diff is larger than max_size, split it into chunks
        if len(file_diff) > max_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            lines = patch.splitlines(keepends=True)
            part_chunk = f"\n--- {filename} ---\n"
            for line in lines:
                while len(line) > max_size:
                    take = max_size - len(part_chunk)
                    if take <= 0:
                        chunks.append(part_chunk)
                        part_chunk = f"\n--- {filename} (continued) ---\n"
                        take = max_size - len(part_chunk)
                    part_chunk += line[:take]
                    chunks.append(part_chunk)
                    part_chunk = f"\n--- {filename} (continued) ---\n"
                    line = line[take:]

                if len(part_chunk) + len(line) > max_size and len(part_chunk) > len(f"\n--- {filename} ---\n"):
                    chunks.append(part_chunk)
                    part_chunk = f"\n--- {filename} (continued) ---\n" + line
                else:
                    part_chunk += line

            if part_chunk.strip() and part_chunk != f"\n--- {filename} ---\n":
                chunks.append(part_chunk)
            continue

        if current_chunk and (len(current_chunk) + len(file_diff) > max_size):
            chunks.append(current_chunk)
            current_chunk = file_diff
        else:
            current_chunk += file_diff

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def check_security(diff: str) -> List[Issue]:
    prompt = f"""
    Analyze this code diff for SECURITY issues only
    (SQL injection, hardcoded secrets, unsafe eval, missing input validation).

    For each issue, determine:
    - severity: HIGH, MEDIUM, or LOW
    - line: the line number where the issue occurs (best estimate)
    - message: a short, specific description

    If there are no issues, return an empty list.

    Diff:
    {diff}
    """

    response = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}],
        response_format=IssueList,
    )

    parsed = response.choices[0].message.parsed
    issues = parsed.issues if parsed else []

    for issue in issues:
        issue.category = "security" 

    return issues

def check_style(diff: str) -> List[Issue]:
    prompt = f"""Review this code diff for style issues only
        (missing type hints, inconsistent naming, unclear variable names).

        For each issue, determine:
            - severity: HIGH, MEDIUM, or LOW
            - line: the line number where the issue occurs (best estimate)
            - message: a short, specific description

        If none, say "No issues found."

        Diff:
        {diff}
        """
    res = client.beta.chat.completions.parse(
        model='gpt-5-nano',
        messages=[{'role':"user", "content":prompt}],
        response_format=IssueList
    )
    parsed = res.choices[0].message.parsed
    issues = parsed.issues if parsed else []

    for issue in issues:
        issue.category = "style"

    return issues

def check_logic(diff: str) -> List[Issue]:
    prompt = f"""Review this code diff for logic bugs only
        (unhandled errors, off-by-one mistakes, missing edge cases).
        For each issue, determine:
            - severity: HIGH, MEDIUM, or LOW
            - line: the line number where the issue occurs (best estimate)
            - message: a short, specific description

        If none, say "No issues found."
        Diff:
        {diff}
        """
    res = client.beta.chat.completions.parse(
        model='gpt-5-nano',
        messages=[{'role':'user', 'content' : prompt}],
        response_format=IssueList
    )
    parsed =  res.choices[0].message.parsed
    issues = parsed.issues if parsed else []

    for issue in issues:
        issue.category = "logic"
    return issues