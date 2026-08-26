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

def check_style(diff:str) -> str:
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
    res = client.chat.completions.parse(
        model='gpt-5-nano',
        messages=[{'role':"user", "content":prompt}],
        response_format=IssueList
    )
    parsed = res.choices[0].message.parsed
    issues = parsed.issues if parsed else []

    for issue in issues:
        issue.category = "style"

    return issues



def check_logic(diff: str) -> str:
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
    res = client.chat.completions.parse(
        model='gpt-5-nano',
        messages=[{'role':'user', 'content' : prompt}],
        response_format=IssueList
    )
    parsed =  res.choices[0].message.parsed
    issues = parsed.issues if parsed else []

    for issue in issues:
        issue.category = "logic"
    return issues