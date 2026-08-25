# app/agent.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_security(diff: str) -> str:
    prompt = f"""Analyze this code diff for security issues only
(SQL injection, hardcoded secrets, unsafe eval).
List issues as bullet points. If none, say "No issues found."

Diff:
{diff}
"""
    response = client.chat.completions.create(
        model="gpt-5-nano-2025-08-07",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def check_style(diff:str) -> str:
    prompt = f"""Review this code diff for style issues only
(missing type hints, inconsistent naming, unclear variable names).
List issues as bullet points. If none, say "No issues found."

Diff:
{diff}
"""
    res = client.chat.completions.create(
        model='gpt-5-nano',
        messages=[{'role':"user", "content":prompt}]
    )
    return res.choices[0].message.content

def check_logic(diff: str) -> str:
    prompt = f"""Review this code diff for logic bugs only
(unhandled errors, off-by-one mistakes, missing edge cases).
List issues as bullet points. If none, say "No issues found."

Diff:
{diff}
"""
    res = client.chat.completions.create(
        model='gpt-5-nano',
        messages=[{'role':'user', 'content' : prompt}]
    )
    return res.choices[0].message.content
