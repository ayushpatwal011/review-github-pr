# 🤖 AI Code Review Agent

An automated code review bot that listens to GitHub Pull Requests and posts AI-generated
review comments — checking for security issues, style violations, and logic bugs — using
a parallel multi-agent pipeline built with **LangGraph**. Includes a **Streamlit UI** so
anyone can run a review on their own repo without touching the API directly.

🔗 **Live demo:** [review-github-pr.streamlit.app](https://review-github-pr.streamlit.app)
🔗 **API:** [review-github-pr.onrender.com/docs](https://review-github-pr.onrender.com/docs)

> Note: the backend runs on Render's free tier, which spins down after inactivity —
> the first request after idle time can take 30-60s to wake up.

---

## Eval Results

The agent's review quality was measured using an **LLM-as-judge** evaluation: a separate
model call is given the original code diff and the agent's flagged issues, and grades
each finding as correct, partially correct, or incorrect, then scores the overall review
quality from 0–100.

| Metric | Score |
|---|---|
| **Average accuracy score** | **96.7 / 100** |
| Evaluation method | LLM-as-judge (GPT-5-nano), 12 labeled test cases |
| Test case categories | Security (SQLi, hardcoded secrets, unsafe eval, command injection, missing validation), Style (naming, type hints), Logic (unhandled errors, off-by-one, None handling), plus clean code controls |

Earlier iterations used keyword/category matching against a fixed expected-issues list,
which reached 90% recall but produced misleadingly low precision — mainly because the
ground-truth test cases didn't account for every legitimate issue the agent correctly
found in a snippet (e.g. flagging missing error handling *in addition to* the SQL
injection the test was designed for). Moving to an LLM-as-judge approach fixed this by
evaluating each finding directly against the diff instead of a fixed keyword list.

---

## How It Works

```
Developer opens/updates a PR on GitHub
        │
        ▼
GitHub sends a webhook  →  POST /webhook  (FastAPI, signature-verified)
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
Results are aggregated into a structured
issue list (severity, confidence, category, line)
        │
        ▼
Bot posts a formatted review comment on the PR
and returns the structured issue array via the API
```

A **Streamlit UI** sits in front of the same backend — anyone can paste in a repo owner,
repo name, PR number, and their own GitHub token to run a review on their own pull
request, without needing to call the API directly.

---

## Why It's Built This Way

| Design choice | Reason |
|---|---|
| **FastAPI + BackgroundTasks** | GitHub webhooks time out after ~10s. The endpoint responds immediately and does the actual AI review work in the background, so deliveries never fail on slow LLM calls. |
| **LangGraph (not a linear script)** | The 3 checks are independent of each other, so they run in parallel instead of one-by-one — nodes return only the state keys they own, avoiding concurrent-write conflicts. |
| **Structured outputs (Pydantic)** | Each check returns a validated `Issue` schema (severity, confidence, category, line, message) instead of free-form text — enabling both a formatted GitHub comment and a machine-readable JSON array for any future frontend. |
| **HMAC signature verification** | The `/webhook` endpoint verifies GitHub's `X-Hub-Signature-256` header using constant-time comparison, rejecting spoofed requests that don't originate from GitHub. |
| **Per-request GitHub tokens** | The Streamlit UI and `/review` endpoint accept a caller-supplied token instead of hardcoding one — so anyone can use this on their own repos with their own credentials. |
| **LLM-as-judge evaluation** | Grading review quality against the actual diff (rather than fixed keyword matching) gives a more reliable accuracy signal and avoids penalizing the agent for correctly finding issues outside a narrow test-case scope. |

---

## Tech Stack

- **FastAPI** — backend API, webhook receiver
- **Streamlit** — user-facing UI for running reviews on any repo
- **LangGraph** — orchestrates parallel AI review checks and merges results
- **OpenAI (GPT-5 nano)** — powers each individual code check and the eval judge
- **GitHub REST API** — fetches PR diffs and posts review comments
- **Render** — backend hosting
- **Streamlit Community Cloud** — UI hosting

---

## Project Structure

```
code-review-agent/
├── app/
│   ├── main.py            # FastAPI app: /webhook and /review endpoints
│   ├── agent.py            # AI check functions (security, style, logic)
│   ├── graph.py             # LangGraph pipeline - parallel checks, aggregation
│   └── github_client.py     # Fetches PR diffs & posts comments via GitHub API
├── eval/
│   ├── test_cases.py        # Labeled test snippets (security/style/logic/clean)
│   ├── judge.py               # LLM-as-judge grading logic
│   └── run_eval.py             # Runs the pipeline + judge, prints accuracy report
├── streamlit_app.py         # Streamlit UI - runs a review on any repo/PR
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
   GITHUB_WEBHOOK_SECRET=your_webhook_secret
   ```

3. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Run the UI (separate terminal):
   ```bash
   streamlit run streamlit_app.py
   ```

5. To receive real GitHub webhooks locally, expose your server with ngrok:
   ```bash
   ngrok http 8000
   ```
   Then add a webhook in your GitHub repo settings pointing to `<ngrok-url>/webhook`,
   content type `application/json`, with a secret matching `GITHUB_WEBHOOK_SECRET`.

---

## Running the Eval Suite

```bash
python -m eval.run_eval
```

This runs all 12 labeled test cases through the full pipeline, judges each result with
an LLM-as-judge call, and prints a per-case breakdown plus the overall average accuracy
score.

---

## Example Output

When a PR is opened, the bot automatically posts:

```
🤖 Automated Code Review

🔴 [HIGH] Line 12 (security) — SQL injection vulnerability: string concatenation
used instead of parameterized query (confidence: 96%)

🟡 [MEDIUM] Line 12 (logic) — No error handling around the database call
(confidence: 82%)

🟢 [LOW] Line 8 (style) — Missing type hints on function parameters (confidence: 74%)
```

---

## What This Project Demonstrates

- Designing an **event-driven agent architecture** (webhook-triggered, not polling)
- Building a **multi-agent pipeline** with parallel execution using LangGraph
- Enforcing **structured outputs** with Pydantic instead of parsing free-text LLM output
- Integrating with a **real external API** (GitHub) using scoped, least-privilege, per-user credentials
- Handling **async/background processing** to meet third-party timeout constraints
- Implementing **security hardening** (HMAC webhook signature verification)
- Building and iterating on an **eval suite**, including recognizing and fixing a flawed
  keyword-matching approach by moving to LLM-as-judge evaluation
- **Deploying** a multi-service system (FastAPI backend + Streamlit frontend) to production hosting

---

## Known Limitations & Future Improvements

- Backend runs on Render's free tier — cold starts add latency after inactivity
- Bot posts a plain comment rather than a formal GitHub Review (Approve/Request Changes) —
  upgrading to the Reviews API would let it actually block merges on critical issues
- No persistent storage of past review results — a `GET /reviews/{pr_number}` endpoint
  backed by a database would let the UI show review history over time
- Rules are currently fixed — a per-repo config file (e.g. `.reviewrc.json`) would let
  teams customize what the bot checks for
