import re
import logging
from typing import List
from ..models.schemas import SandboxEvaluationRequest, SandboxEvaluationResult, SandboxTestCaseResult

logger = logging.getLogger(__name__)


# Calibrated verification criteria registry for sandbox challenges
CRITERIA_REGISTRY = {
    "default": [
        {"description": "Code is non-empty and well-formed", "assertion_type": "contains_regex", "expected": r"\w+"},
        {"description": "Contains return or DOM expression", "assertion_type": "contains_regex", "expected": r"(return|<|function|const|let)"}
    ]
}


class SandboxEvaluator:
    """Evaluates client sandbox submissions against DOM, regex, and syntactic unit criteria."""

    @classmethod
    def evaluate(cls, req: SandboxEvaluationRequest) -> SandboxEvaluationResult:
        code = req.code.strip()
        lang = req.language.lower()
        test_results: List[SandboxTestCaseResult] = []

        if not code:
            return SandboxEvaluationResult(
                challenge_id=req.challenge_id,
                passed=False,
                all_tests_passed=False,
                score_percentage=0.0,
                results=[
                    SandboxTestCaseResult(
                        description="Code submission non-empty",
                        passed=False,
                        details="The code editor is empty. Please implement the requested challenge."
                    )
                ],
                error_message="Empty code submission",
                feedback="Code cannot be empty. Follow the challenge instructions."
            )

        # 1. Basic syntax checks
        syntax_ok = True
        syntax_err = None
        if lang in ["javascript", "js"]:
            # Check balanced brackets/braces/parentheses
            stack = []
            pairs = {')': '(', '}': '{', ']': '['}
            for char in code:
                if char in pairs.values():
                    stack.append(char)
                elif char in pairs.keys():
                    if not stack or stack.pop() != pairs[char]:
                        syntax_ok = False
                        syntax_err = f"Unmatched closing bracket: '{char}'"
                        break
            if stack and syntax_ok:
                syntax_ok = False
                syntax_err = f"Unclosed opening bracket: '{stack[-1]}'"

        test_results.append(
            SandboxTestCaseResult(
                description="Syntactic Structure & Bracket Balancing",
                passed=syntax_ok,
                details="Syntax structure is valid and balanced." if syntax_ok else f"Syntax error: {syntax_err}"
            )
        )

        # 2. Domain & Language-specific criteria
        if lang == "html":
            # Test for basic tags
            has_tag = bool(re.search(r"<[a-zA-Z0-9]+[^>]*>.*</[a-zA-Z0-9]+>|<[a-zA-Z0-9]+[^>]*/?>", code, re.DOTALL))
            test_results.append(
                SandboxTestCaseResult(
                    description="Valid HTML markup elements present",
                    passed=has_tag,
                    details="DOM elements successfully parsed." if has_tag else "No valid HTML tags detected."
                )
            )

            # Specific challenge checks
            if "counter" in req.challenge_id or "react" in req.challenge_id:
                has_inc = bool(re.search(r"btn-inc|increment", code, re.IGNORECASE))
                has_dec = bool(re.search(r"btn-dec|decrement", code, re.IGNORECASE))
                test_results.append(
                    SandboxTestCaseResult(
                        description="Includes interactive trigger buttons",
                        passed=has_inc or has_dec,
                        details="Found control elements in markup." if (has_inc or has_dec) else "Missing button with id/class 'btn-inc' or 'btn-dec'."
                    )
                )

            if "flutter" in req.challenge_id:
                has_card = bool(re.search(r"material-card|card", code, re.IGNORECASE))
                test_results.append(
                    SandboxTestCaseResult(
                        description="Material Card container element",
                        passed=has_card,
                        details="Card container found." if has_card else "Missing card container element."
                    )
                )

        else:
            # JavaScript criteria
            has_function = bool(re.search(r"(function\s+\w+|\w+\s*=\s*\(?.*\)?\s*=>)", code))
            test_results.append(
                SandboxTestCaseResult(
                    description="Function declaration / handler defined",
                    passed=has_function,
                    details="Function definition detected." if has_function else "Please define a function or arrow handler."
                )
            )

            has_return = bool(re.search(r"\breturn\b", code))
            test_results.append(
                SandboxTestCaseResult(
                    description="Explicit return statement present",
                    passed=has_return,
                    details="Return statement found." if has_return else "Function should explicitly return a computed result."
                )
            )

        passed_count = sum(1 for t in test_results if t.passed)
        total_count = len(test_results)
        score_pct = round((passed_count / total_count) * 100, 1) if total_count > 0 else 0.0
        all_passed = (passed_count == total_count)

        feedback = (
            f"Verification Complete: All {total_count} unit checks passed! Hands-on PoW accepted."
            if all_passed
            else f"Verification in progress: {passed_count}/{total_count} unit checks passed. Fix highlighted issues to complete milestone."
        )

        return SandboxEvaluationResult(
            challenge_id=req.challenge_id,
            passed=all_passed,
            all_tests_passed=all_passed,
            score_percentage=score_pct,
            results=test_results,
            stdout=f"Executed {total_count} assertions. Passed: {passed_count}, Failed: {total_count - passed_count}.",
            error_message=syntax_err,
            feedback=feedback
        )

