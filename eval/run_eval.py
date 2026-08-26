import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.graph import compiled_graph
from eval.test_cases import TEST_CASES
from eval.judge import judge_review


def run_case(case: dict) -> dict:
    result = compiled_graph.invoke({
        "diff": case["diff"],
        "security_result": [], "style_result": [], "logic_result": [],
        "all_issues": [], "final_comment": ""
    })
    detected = [issue.model_dump() for issue in result["all_issues"]]

    judgment = judge_review(case["diff"], detected)

    return {
        "id": case["id"],
        "detected_count": len(detected),
        "accuracy_score": judgment.accuracy_score,
        "judged_issues": [j.model_dump() for j in judgment.judged_issues],
        "missed_issues": judgment.missed_issues,
        "overall_reasoning": judgment.overall_reasoning,
    }


def main():
    results = [run_case(case) for case in TEST_CASES]

    avg_score = sum(r["accuracy_score"] for r in results) / len(results)

    print("=" * 70)
    print("LLM-AS-JUDGE EVAL REPORT")
    print("=" * 70)

    for r in results:
        print(f"\n[{r['id']}]  Accuracy Score: {r['accuracy_score']}/100")
        print(f"  Reasoning: {r['overall_reasoning']}")
        for ji in r["judged_issues"]:
            mark = {"CORRECT": "✅", "PARTIALLY_CORRECT": "🟡", "INCORRECT": "❌"}[ji["verdict"]]
            print(f"    {mark} {ji['verdict']}: {ji['original_message']}")
            print(f"       → {ji['reasoning']}")
        if r["missed_issues"]:
            print(f"  ⚠️ Missed:")
            for m in r["missed_issues"]:
                print(f"    - {m}")

    print("\n" + "=" * 70)
    print(f"AVERAGE ACCURACY SCORE: {avg_score:.1f} / 100")
    print("=" * 70)

    with open("eval/judge_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results saved to eval/judge_results.json")


if __name__ == "__main__":
    main()