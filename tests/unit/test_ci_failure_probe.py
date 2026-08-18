"""Day 54 CI failure drill.

This test is intentionally wrong and must be removed after verifying that a
failed pytest step still uploads JUnit and Allure results as an artifact.
"""


def test_ci_failure_still_archives_reports():
    actual_status = "failed"
    expected_status = "passed"

    assert actual_status == expected_status, (
        "intentional Day 54 failure: verify that CI remains red while the "
        "test-results artifact is still uploaded"
    )
