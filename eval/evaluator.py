"""Core evaluation logic for the MCP server evaluation framework."""

import csv
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

import anthropic

from .eval_methods import evaluate_numeric, evaluate_string, evaluate_llm_judge


@dataclass
class EvalResult:
    """Result of evaluating a single question."""
    question: str
    expected_answer: str
    eval_type: str
    model_response: str
    passed: bool
    details: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class EvalSummary:
    """Summary of all evaluation results."""
    total: int
    passed: int
    failed: int
    pass_rate: float
    by_eval_type: dict = field(default_factory=dict)
    results: list[EvalResult] = field(default_factory=list)


class Evaluator:
    """Evaluates MCP server responses against expected answers."""

    def __init__(self, server_url: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the evaluator.

        Args:
            server_url: URL of the MCP server to evaluate
            model: Claude model to use for generating responses
        """
        self.server_url = server_url
        self.model = model
        self.client = anthropic.Anthropic()

    def load_questions(self, csv_path: str | Path) -> list[dict]:
        """Load questions from a CSV file.

        Args:
            csv_path: Path to the CSV file with questions

        Returns:
            List of question dictionaries with 'question', 'expected_answer', 'eval_type'
        """
        questions = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions.append({
                    "question": row["question"],
                    "expected_answer": row["expected_answer"],
                    "eval_type": row["eval_type"]
                })
        return questions

    def call_model_with_mcp(self, question: str) -> str:
        """Call Claude with the MCP server to answer a question.

        Args:
            question: The question to ask

        Returns:
            The model's response text
        """
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=4096,
            betas=["mcp-client-2025-04-04"],
            mcp_servers=[
                {
                    "type": "url",
                    "url": self.server_url,
                    "name": "nih-reporter"
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        # Extract text from response
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        return "\n".join(text_parts)

    def evaluate_response(
        self,
        question: str,
        expected_answer: str,
        eval_type: str,
        model_response: str
    ) -> EvalResult:
        """Evaluate a model response against the expected answer.

        Args:
            question: The original question
            expected_answer: The expected answer
            eval_type: Type of evaluation ('numeric', 'string', 'llm_judge')
            model_response: The model's response

        Returns:
            EvalResult with pass/fail status and details
        """
        try:
            if eval_type == "numeric":
                result = evaluate_numeric(
                    model_response, expected_answer,
                    question=question, client=self.client
                )
            elif eval_type == "string":
                result = evaluate_string(model_response, expected_answer)
            elif eval_type == "llm_judge":
                result = evaluate_llm_judge(
                    question, model_response, expected_answer, self.client
                )
            else:
                return EvalResult(
                    question=question,
                    expected_answer=expected_answer,
                    eval_type=eval_type,
                    model_response=model_response,
                    passed=False,
                    error=f"Unknown eval_type: {eval_type}"
                )

            return EvalResult(
                question=question,
                expected_answer=expected_answer,
                eval_type=eval_type,
                model_response=model_response,
                passed=result["passed"],
                details=result
            )

        except Exception as e:
            return EvalResult(
                question=question,
                expected_answer=expected_answer,
                eval_type=eval_type,
                model_response=model_response,
                passed=False,
                error=str(e)
            )

    def run_evaluation(
        self,
        questions: list[dict],
        verbose: bool = False
    ) -> EvalSummary:
        """Run evaluation on a list of questions.

        Args:
            questions: List of question dicts with 'question', 'expected_answer', 'eval_type'
            verbose: Whether to print progress

        Returns:
            EvalSummary with results and statistics
        """
        results = []
        by_eval_type = {}

        for i, q in enumerate(questions):
            if verbose:
                print(f"Evaluating question {i+1}/{len(questions)}: {q['question'][:50]}...")

            # Call model with MCP server
            try:
                model_response = self.call_model_with_mcp(q["question"])
            except Exception as e:
                model_response = ""
                result = EvalResult(
                    question=q["question"],
                    expected_answer=q["expected_answer"],
                    eval_type=q["eval_type"],
                    model_response=model_response,
                    passed=False,
                    error=f"API call failed: {e}"
                )
                results.append(result)
                continue

            # Evaluate the response
            result = self.evaluate_response(
                q["question"],
                q["expected_answer"],
                q["eval_type"],
                model_response
            )
            results.append(result)

            # Track by eval type
            eval_type = q["eval_type"]
            if eval_type not in by_eval_type:
                by_eval_type[eval_type] = {"total": 0, "passed": 0}
            by_eval_type[eval_type]["total"] += 1
            if result.passed:
                by_eval_type[eval_type]["passed"] += 1

            if verbose:
                status = "PASS" if result.passed else "FAIL"
                print(f"  Result: {status}")

        # Calculate summary
        total = len(results)
        passed = sum(1 for r in results if r.passed)

        return EvalSummary(
            total=total,
            passed=passed,
            failed=total - passed,
            pass_rate=passed / total if total > 0 else 0.0,
            by_eval_type=by_eval_type,
            results=results
        )

    def save_results(
        self,
        summary: EvalSummary,
        output_dir: str | Path,
        filename_prefix: str = "eval"
    ) -> Path:
        """Save evaluation results to a JSON file.

        Args:
            summary: The evaluation summary to save
            output_dir: Directory to save results
            filename_prefix: Prefix for the output filename

        Returns:
            Path to the saved results file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        output_path = output_dir / filename

        # Convert to serializable format
        output_data = {
            "summary": {
                "total": summary.total,
                "passed": summary.passed,
                "failed": summary.failed,
                "pass_rate": summary.pass_rate,
                "by_eval_type": summary.by_eval_type
            },
            "results": [asdict(r) for r in summary.results],
            "metadata": {
                "server_url": self.server_url,
                "model": self.model,
                "timestamp": timestamp
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        return output_path
