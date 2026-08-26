# streamlit_app.py
import streamlit as st
import requests
import os

st.set_page_config(page_title="AI Code Review Agent", page_icon="🤖", layout="centered")

st.title("🤖 AI Code Review Agent")
st.caption("Run an automated security, style & logic review on any public GitHub pull request.")

import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

with st.form("review_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Repo owner", placeholder="e.g. octocat")
    with col2:
        repo = st.text_input("Repo name", placeholder="e.g. Hello-World")

    pr_number = st.number_input("Pull Request number", min_value=1, step=1)

    github_token = st.text_input(
        "Your GitHub token",
        type="password",
        help="Needs 'repo' scope. Only used for this request, never stored. "
             "Create one at github.com/settings/tokens"
    )

    submitted = st.form_submit_button("Run Review", use_container_width=True)

if submitted:
    if not (owner and repo and pr_number and github_token):
        st.error("Please fill in all fields, including your GitHub token.")
    else:
        with st.spinner("Fetching diff and running security, style & logic checks..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/review",
                    json={
                        "owner": owner,
                        "repo": repo,
                        "pr_number": int(pr_number),
                        "github_token": github_token,
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
                st.stop()

        if data.get("message") == "No changes found to review":
            st.info("No changes found in this PR to review.")
        else:
            issues = data.get("issues", [])
            st.success(f"Review posted to PR #{pr_number} on GitHub — {len(issues)} issue(s) found.")

            if not issues:
                st.balloons()
                st.write("✅ No issues found. Clean PR!")
            else:
                severity_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

                for issue in sorted(issues, key=lambda i: severity_order[i["severity"]]):
                    with st.container(border=True):
                        st.markdown(
                            f"{severity_color[issue['severity']]} **{issue['severity']}** "
                            f"· `{issue['category']}` · Line {issue['line']} "
                        )
                        st.write(issue["message"])

st.divider()
st.caption(
    "Built with FastAPI + LangGraph. Your token is sent directly to the backend for "
    "this request only and is never logged or stored."
)