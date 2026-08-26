from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from app.github_client import get_pr_diff, post_pr_comment
from app.graph import compiled_graph
import hmac
import hashlib
import os

app = FastAPI()

class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    github_token: str | None = None

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Compare GitHub's signature against one we compute ourselves."""
    if not signature_header:
        return False

    expected = hmac.new(
        key=WEBHOOK_SECRET.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    expected_header = f"sha256={expected}"

    return hmac.compare_digest(expected_header, signature_header)


def run_review(diff: str) -> dict:
    """Runs the LangGraph pipeline and returns the final state."""
    return compiled_graph.invoke({
        "diff": diff,
        "security_result": [],
        "style_result": [],
        "logic_result": [],
        "all_issues": [],
        "final_comment": ""
    })


def process_review(owner: str, repo: str, pr_number: int):
    """Runs in the background, after we've already responded to GitHub."""
    diff = get_pr_diff(owner, repo, pr_number)
    if not diff.strip():
        return

    result = run_review(diff)
    post_pr_comment(owner, repo, pr_number, result["final_comment"])


@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"message": f"Ignored action: {action}"}

    pr = payload.get("pull_request")
    if not pr:
        return {"message": "Not a PR event"}

    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = pr["number"]

 
    background_tasks.add_task(process_review, owner, repo, pr_number)

    return {"message": "Review queued", "pr": pr_number}


@app.post("/review")
def review_code(request: ReviewRequest):
    diff = get_pr_diff(request.owner, request.repo, request.pr_number, token=request.github_token)

    if not diff.strip():
        return {"message": "No changes found to review"}

    result = run_review(diff)

    post_pr_comment(request.owner, request.repo, request.pr_number, result["final_comment"], token=request.github_token)

    return {
        "message": "Review posted",
        "issues": [issue.model_dump() for issue in result["all_issues"]]
    }