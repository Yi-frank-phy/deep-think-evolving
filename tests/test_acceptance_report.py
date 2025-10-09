from scripts.generate_acceptance_report import generate_acceptance_report


def test_generate_acceptance_report_success():
    log_lines = [
        "[Spec-STEP] Step 1: Generating strategic blueprint",
        "[Spec-OK] Generated 2 strategies.",
        "[Spec-DATA] Strategy 1: Alpha",
        "[Spec-STEP] Step 2: Embedding strategies",
        "[Spec-OK] Strategies embedded successfully.",
        "[Spec-FILE] Summary updated for strategy-01 (stored at /tmp/summary.md)",
        "[Spec-STEP] Step 3: Calculating cosine similarity matrix",
        "[Spec-OK] Similarity matrix calculated.",
        "[Spec-OK] Pipeline execution completed.",
    ]

    report = generate_acceptance_report(log_lines)

    assert report["overall_status"] == "pass"
    assert report["tasks"], "Tasks should not be empty"
    assert all(task["status"] == "pass" for task in report["tasks"])
    assert "/tmp/summary.md" in "\n".join(report["files"])


def test_generate_acceptance_report_failure():
    log_lines = [
        "[Spec-STEP] Step 1: Generating strategic blueprint",
        "[Spec-ERR] Failed to generate strategic blueprint.",
    ]

    report = generate_acceptance_report(log_lines)

    assert report["overall_status"] == "fail"
    assert report["tasks"], "Tasks should not be empty"
    assert report["tasks"][0]["status"] == "fail"
