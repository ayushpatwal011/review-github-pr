# 🤖 AI Code Review Agent

An automated code review bot that listens to GitHub Pull Requests and posts AI-generated
review comments — checking for security issues, style violations, and logic bugs — using
a parallel multi-agent pipeline built with **LangGraph**.

---

## How It Works

```
Developer opens/updates a PR on GitHub
        │
        ▼
GitHub sends a webhook  →  POST /webhook  (FastAPI)
        │
        ▼
FastAPI responds instantly (200 OK)
and queues the review as a background task
        │
        ▼
Background task fetches the real PR diff
via the GitHub API
        │
        ▼
LangGraph runs 3 checks IN PARALLEL:
   ├── Security Check   (SQL injection, hardcoded secrets, unsafe eval)
   ├── Style Check       (naming, type hints, formatting)
   └── Logic Check        (unhandled errors, edge cases)
        │
        ▼
Results are aggregated into one report
        │
        ▼
Bot posts the review as a comment
directly on the Pull Request
```

---

## Why It's Built This Way

| Design choice | Reason |
|---|---|
| **FastAPI + BackgroundTasks** | GitHub webhooks time out after ~10s. The endpoint responds immediately and does the actual AI review work in the background, so deliveries never fail on slow LLM calls. |
| **LangGraph (not a linear script)** | The 3 checks are independent of each other, so they run in parallel instead of one-by-one — this models the real workflow shape (fan-out → aggregate) instead of forcing it into a straight line. |
| **GitHub App/Token scoped narrowly** | The token only has permission to read PR diffs and post comments — it cannot merge, delete, or push code, following least-privilege access. |
| **Structured, single-responsibility functions** | Each check (`check_security`, `check_style`, `check_logic`) is a separate, testable function — easy to extend with new checks later. |

---

## Tech Stack

- **FastAPI** — receives GitHub webhooks, exposes the `/webhook` and `/review` endpoints
- **LangGraph** — orchestrates parallel AI review checks and merges results
- **OpenAI (GPT-5 nano)** — powers each individual code check
- **GitHub REST API** — fetches PR diffs and posts review comments
- **ngrok** — exposes the local server to GitHub during development

---

## Project Structure

```
code-review-agent/
├── app/
│   ├── main.py            # FastAPI app: /webhook and /review endpoints
│   ├── agent.py            # Individual AI check functions (security, style, logic)
│   ├── graph.py             # LangGraph pipeline - runs checks in parallel, aggregates results
│   └── github_client.py     # Fetches PR diffs & posts comments via GitHub API
├── .env                     # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

1. Clone the repo and create a virtual environment
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

2. Create a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_key
   GITHUB_TOKEN=your_github_token
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Expose it publicly (for GitHub webhooks) with ngrok:
   ```bash
   ngrok http 8000
   ```

5. Add a webhook in your GitHub repo settings:
   - Payload URL: `https://<your-ngrok-url>/webhook`
   - Content type: `application/json`
   - Events: Pull requests

---

## Example Output

When a PR is opened, the bot automatically posts:

```
🤖 Automated Code Review

### 🔴 Security
- SQL injection vulnerability: string concatenation used instead of parameterized query
- Hardcoded API key found in source code

### 🟡 Style
- Missing type hints on function parameters

### 🟠 Logic
- No error handling for the case where the database query returns no results
```

---

## What This Project Demonstrates

- Designing an **event-driven agent architecture** (webhook-triggered, not polling)
- Building a **multi-agent pipeline** with parallel execution using LangGraph
- Integrating an agent with a **real external API** (GitHub) with scoped, least-privilege access
- Handling **async/background processing** to meet third-party timeout constraints
- Structuring an agentic AI system for **extensibility** (new checks can be added as new graph nodes)

---

## Possible Future Improvements

- Add an eval suite measuring detection accuracy against known vulnerable code samples
- Add webhook signature verification (`X-Hub-Signature-256`) for production security
- Use GitHub's Review API to block/approve PRs, not just comment
- Deploy to a persistent host (Render/Railway) instead of local + ngrok


## for developer
GitHub PR opened
   → POST /webhook  (main.py)
       → action check passes
       → background_tasks.add_task(process_review)
       → returns instantly (GitHub happy, no timeout)
             │
             ▼ (runs after response is sent)
   process_review(owner, repo, pr_number)
       → get_pr_diff()          [github_client.py]
       → compiled_graph.invoke() [graph.py]
             → security_node → check_security()   [agent.py] ─┐
             → style_node    → check_style()       [agent.py] ─┼─ run in parallel
             → logic_node    → check_logic()        [agent.py] ─┘
             → aggregate_node → formats final_comment
       → post_pr_comment()        [github_client.py]
             → real comment appears on your GitHub PR