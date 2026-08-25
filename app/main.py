from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
from pydantic import BaseModel
from app.agent import check_security, check_logic, check_style
from app.github_client import get_pr_diff, post_pr_comment
from app.graph import compiled_graph


app = FastAPI()

class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int

@app.post("/review")
def review_code(request: ReviewRequest):
    diff = get_pr_diff(request.owner, request.repo, request.pr_number)

    if not diff.strip():
        return {"message": "No changes found to review"}

    result = check_security(diff)

    post_pr_comment(
        request.owner, request.repo, request.pr_number,
        f"🤖 **Automated Security Review**\n\n{result}"
    )

    return {"issues": result, "posted_to_pr": True}


def process_review(owner: str, repo: str, pr_number: int):
    diff = get_pr_diff(owner, repo, pr_number)
    if not diff.strip():
        return

    result = compiled_graph.invoke({
        "diff": diff,
        "security_result": "", "style_result": "", "logic_result": "", "final_comment": ""
    })

    post_pr_comment(owner, repo, pr_number, result["final_comment"])


@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
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
     # Queue the slow work, respond to GitHub IMMEDIATELY
    background_tasks.add_task(process_review, owner, repo, pr_number)

    diff = get_pr_diff(owner, repo, pr_number)
    if not diff.strip():
        return {"message": "No changes to review"}

    result = check_security(diff)

    post_pr_comment(owner, repo, pr_number, f"🤖 **Automated Security Review**\n\n{result}")

    return {"message": "Review posted", "pr": pr_number}