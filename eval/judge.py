from pydantic import BaseModel, Field
from typing import List, Literal
from openai import OpenAI

client = OpenAI()
_ = client.beta.chat.completions  # force import before any parallel use elsewhere

class JudgedIssue(BaseModel):
    original_message: str
    verdict: Literal["CORRECT", "PARTIALLY_CORRECT", "INCORRECT"]
    reasoning: str

class JudgeResult(BaseModel):
    judged_issues: List[JudgedIssue]
    missed_issues: List[str] = Field(
        description="Genuinely important real issues in the diff that were NOT flagged at all"
    )
    accuracy_score: int = Field(
        ge=0, le=100,
        description="Overall score 0-100: how good was this review, considering "
                     "both correctness of flagged issues and whether anything important was missed"
    )
    overall_reasoning: str


def judge_review(diff: str, detected_issues: list[dict]) -> JudgeResult:
    issues_text = "\n".join(
        f"- [{i['severity']}] ({i['category']}) Line {i['line']}: {i['message']}"
        for i in detected_issues
    ) or "(no issues were flagged)"

    prompt = f"""You are a senior software engineer acting as a judge, evaluating an AI
code review bot's output against the actual code.

CODE DIFF:
{diff}

ISSUES THE BOT FLAGGED:
{issues_text}

Your job:
1. For EACH flagged issue, decide if it's CORRECT (genuinely a real, valid issue in
   this diff), PARTIALLY_CORRECT (technically true but minor/debatable/low value),
   or INCORRECT (wrong, hallucinated, or doesn't apply to this code).
2. Separately, list any IMPORTANT real issues in the diff that the bot completely
   missed (only include genuinely significant ones — security bugs, real logic bugs
   — not nitpicks).
3. Give an overall accuracy_score from 0-100 reflecting review quality: a review with
   all-correct, non-redundant, well-targeted issues and nothing important missed should
   score high (90+). A review with many wrong/hallucinated issues or missed critical
   bugs should score low.

Be a strict but fair reviewer — the kind of engineer who wants tools to actually be
useful, not one who nitpicks for the sake of it.
"""

    response = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}],
        response_format=JudgeResult,
    )
    return response.choices[0].message.parsed