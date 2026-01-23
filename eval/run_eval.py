#!/usr/bin/env python3
"""CLI entry point for MCP server evaluation."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .evaluator import Evaluator

# Load environment variables from .env file
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate MCP server accuracy against known questions and answers"
    )
    parser.add_argument(
        "server_url",
        help="URL of the MCP server to evaluate"
    )
    parser.add_argument(
        "-q", "--questions",
        default=None,
        help="Path to questions CSV file (default: eval/questions.csv)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory for results (default: eval/results)"
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress"
    )

    args = parser.parse_args()

    # Determine paths
    eval_dir = Path(__file__).parent
    questions_path = Path(args.questions) if args.questions else eval_dir / "questions.csv"
    output_dir = Path(args.output) if args.output else eval_dir / "results"

    # Validate questions file exists
    if not questions_path.exists():
        print(f"Error: Questions file not found: {questions_path}", file=sys.stderr)
        sys.exit(1)

    # Create evaluator
    evaluator = Evaluator(server_url=args.server_url, model=args.model)

    # Load questions
    print(f"Loading questions from {questions_path}...")
    questions = evaluator.load_questions(questions_path)
    print(f"Loaded {len(questions)} questions")

    # Run evaluation
    print(f"\nEvaluating against {args.server_url}...")
    print("-" * 50)

    summary = evaluator.run_evaluation(questions, verbose=args.verbose)

    # Print summary
    print("-" * 50)
    print("\nEvaluation Summary")
    print("=" * 50)
    print(f"Total questions: {summary.total}")
    print(f"Passed: {summary.passed}")
    print(f"Failed: {summary.failed}")
    print(f"Pass rate: {summary.pass_rate:.1%}")

    if summary.by_eval_type:
        print("\nBy evaluation type:")
        for eval_type, stats in summary.by_eval_type.items():
            type_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {eval_type}: {stats['passed']}/{stats['total']} ({type_rate:.1%})")

    # Print failed questions
    failed_results = [r for r in summary.results if not r.passed]
    if failed_results:
        print(f"\nFailed questions ({len(failed_results)}):")
        for r in failed_results:
            print(f"\n  Q: {r.question[:80]}...")
            print(f"  Expected: {r.expected_answer[:50]}...")
            if r.error:
                print(f"  Error: {r.error}")
            else:
                print(f"  Details: {r.details.get('details', 'N/A')}")

    # Save results
    output_path = evaluator.save_results(summary, output_dir)
    print(f"\nResults saved to: {output_path}")

    # Exit with non-zero if any failures
    sys.exit(0 if summary.failed == 0 else 1)


if __name__ == "__main__":
    main()
