# app/graph.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from app.agent import check_security, check_style, check_logic, Issue

class ReviewState(TypedDict):
    diff: str
    security_result: List[Issue]
    style_result: List[Issue]
    logic_result: List[Issue]
    all_issues: List[Issue]
    final_comment: str


def security_node(state: ReviewState) -> dict:
    return {"security_result": check_security(state["diff"])}

def style_node(state: ReviewState) -> dict:
    return {"style_result": check_style(state["diff"])}

def logic_node(state: ReviewState) -> dict:
    return {"logic_result": check_logic(state["diff"])}

def aggregate_node(state: ReviewState) -> dict:
    all_issues = state["security_result"] + state["style_result"] + state["logic_result"]

    if not all_issues:
        return {
            "all_issues": [],
            "final_comment": "## 🤖 Automated Code Review\n\n✅ No issues found. Looks good!"
        }

    emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    comment = "## 🤖 Automated Code Review\n\n"
    for issue in sorted(all_issues, key=lambda i: order[i.severity]):
        comment += (
            f"{emoji[issue.severity]} **[{issue.severity}]** `Line {issue.line}` "
            f"({issue.category}) — {issue.message} \n\n "
        )

    return {"all_issues": all_issues, "final_comment": comment}


graph = StateGraph(ReviewState)

graph.add_node("security_check", security_node)
graph.add_node("style_check", style_node)
graph.add_node("logic_check", logic_node)
graph.add_node("aggregate", aggregate_node)

graph.add_edge(START, "security_check")
graph.add_edge(START, "style_check")
graph.add_edge(START, "logic_check")

graph.add_edge("security_check", "aggregate")
graph.add_edge("style_check", "aggregate")
graph.add_edge("logic_check", "aggregate")

graph.add_edge("aggregate", END)

compiled_graph = graph.compile()