# app/graph.py
from langgraph.graph import StateGraph, END, START
from typing import TypedDict
from app.agent import check_security, check_style, check_logic

# Shared data that flows through the graph
class ReviewState(TypedDict):
    diff: str
    security_result: str
    style_result: str
    logic_result: str
    final_comment: str

# Each node just fills in ONE field of the state
def security_node(state: ReviewState) -> ReviewState:
    state["security_result"] = check_security(state["diff"])
    return state

def style_node(state: ReviewState) -> ReviewState:
    state["style_result"] = check_style(state["diff"])
    return state

def logic_node(state: ReviewState) -> ReviewState:
    state["logic_result"] = check_logic(state["diff"])
    return state

def aggregate_node(state: ReviewState) -> ReviewState:
    state["final_comment"] = f"""🤖 **Automated Code Review**

### 🔴 Security
{state['security_result']}

### 🟡 Style
{state['style_result']}

### 🟠 Logic
{state['logic_result']}
"""
    return state


graph = StateGraph(ReviewState)
graph.add_node("security_check", security_node)
graph.add_node("style_check", style_node)
graph.add_node("logic_check", logic_node)
graph.add_node("aggregate", aggregate_node)

# All 3 start in parallel from START
graph.add_edge(START, "security_check")
graph.add_edge(START, "style_check")
graph.add_edge(START, "logic_check")


graph.add_edge("security_check", "aggregate")
graph.add_edge("style_check", "aggregate")
graph.add_edge("logic_check", "aggregate")

graph.add_edge("aggregate", END)
compiled_graph = graph.compile()