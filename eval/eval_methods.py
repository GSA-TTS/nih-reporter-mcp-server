"""Evaluation method implementations for comparing model responses to expected answers."""

import re
from difflib import SequenceMatcher
import anthropic


def extract_number(text: str) -> float | None:
    """Extract the first number from a text string.

    Handles integers, floats, and numbers with commas (e.g., "1,234").
    """
    # Remove commas from numbers
    text = text.replace(",", "")

    # Find all numbers (including decimals and negative)
    numbers = re.findall(r"-?\d+\.?\d*", text)

    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return None
    return None


def parse_number(text: str) -> float | None:
    """Parse a number string, handling commas."""
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def extract_all_numbers(text: str) -> list[float]:
    """Extract all numbers from text."""
    text_clean = text.replace(",", "")
    matches = re.findall(r"-?\d+\.?\d*", text_clean)
    result = []
    for m in matches:
        try:
            result.append(float(m))
        except ValueError:
            pass
    return result


def is_likely_year(num: float, expected_hint: float | None) -> bool:
    """Check if number looks like a year (1900-2100) unless expected is in that range."""
    if expected_hint and 1900 <= expected_hint <= 2100:
        return False  # Expected answer is a year, don't filter
    return 1900 <= num <= 2100 and num == int(num)


def extract_number_with_llm(
    text: str, question: str, client: anthropic.Anthropic
) -> float | None:
    """Use Claude Haiku to extract the numeric answer from response text."""
    prompt = f"""Extract ONLY the numeric answer from this response to the question.

Question: {question}
Response: {text}

Reply with just the number (no commas, no units, no explanation). If no clear answer, reply "NONE"."""

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )

    result = message.content[0].text.strip()
    if result.upper() == "NONE":
        return None
    try:
        return float(result.replace(",", ""))
    except ValueError:
        return None


def extract_number_smart(
    text: str,
    question: str = "",
    expected_hint: float | None = None,
    client: anthropic.Anthropic | None = None
) -> tuple[float | None, str]:
    """Extract a number using multiple strategies.

    Returns:
        Tuple of (extracted_value, method_used)
    """
    # Strategy 1: Bold pattern - **123,456** or **123,456 words**
    bold_pattern = r'\*\*[\s]*([0-9,]+(?:\.[0-9]+)?)'
    bold_matches = re.findall(bold_pattern, text)
    if bold_matches:
        for match in bold_matches:
            num = parse_number(match)
            if num and not is_likely_year(num, expected_hint):
                return (num, "bold_pattern")

    # Strategy 2: Answer phrases
    answer_patterns = [
        r'(?:is|are|received|totals?|found)\s+\*?\*?([0-9,]+)',
        r'([0-9,]+)\s+(?:total|grants?|projects?|awards?)',
    ]
    for pattern in answer_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            num = parse_number(match)
            if num and not is_likely_year(num, expected_hint):
                return (num, "answer_phrase")

    # Strategy 3: Filter years from all numbers, take first non-year
    all_numbers = extract_all_numbers(text)
    non_year_numbers = [n for n in all_numbers if not is_likely_year(n, expected_hint)]
    if non_year_numbers:
        return (non_year_numbers[0], "first_non_year")

    # Strategy 4: LLM fallback
    if client:
        llm_result = extract_number_with_llm(text, question, client)
        if llm_result:
            return (llm_result, "llm_extraction")

    # Fallback: original behavior (first number found)
    return (extract_number(text), "first_number")


def evaluate_numeric(
    response: str,
    expected: str | float | int,
    tolerance: float = 0.05,
    question: str = "",
    client: anthropic.Anthropic | None = None
) -> dict:
    """Evaluate a numeric response against an expected value.

    Args:
        response: The model's response text
        expected: The expected numeric value (as string or number)
        tolerance: Relative tolerance for comparison (default 5%)
        question: The original question (used for LLM extraction fallback)
        client: Anthropic client (used for LLM extraction fallback)

    Returns:
        dict with 'passed', 'extracted_value', 'expected_value', 'extraction_method',
        and 'details'
    """
    # Convert expected to float
    if isinstance(expected, str):
        expected_value = extract_number(expected)
    else:
        expected_value = float(expected)

    if expected_value is None:
        return {
            "passed": False,
            "extracted_value": None,
            "expected_value": expected,
            "extraction_method": None,
            "details": "Could not parse expected value as a number"
        }

    # Extract number from response using smart extraction
    extracted_value, extraction_method = extract_number_smart(
        response, question, expected_value, client
    )

    if extracted_value is None:
        return {
            "passed": False,
            "extracted_value": None,
            "expected_value": expected_value,
            "extraction_method": extraction_method,
            "details": "Could not extract a number from the response"
        }

    # Calculate relative difference
    if expected_value == 0:
        passed = extracted_value == 0
        diff = abs(extracted_value)
    else:
        diff = abs(extracted_value - expected_value) / abs(expected_value)
        passed = diff <= tolerance

    return {
        "passed": passed,
        "extracted_value": extracted_value,
        "expected_value": expected_value,
        "extraction_method": extraction_method,
        "details": f"Difference: {diff:.2%} (tolerance: {tolerance:.2%})"
    }


def evaluate_string(
    response: str,
    expected: str,
    fuzzy_threshold: float = 0.8
) -> dict:
    """Evaluate a string response against an expected value.

    First attempts exact match (case-insensitive), then falls back to
    fuzzy matching using sequence similarity.

    Args:
        response: The model's response text
        expected: The expected string value
        fuzzy_threshold: Minimum similarity ratio for fuzzy match (0-1)

    Returns:
        dict with 'passed', 'match_type', 'similarity', and 'details'
    """
    response_lower = response.lower()
    expected_lower = expected.lower()

    # Check for exact match (case-insensitive)
    if expected_lower in response_lower:
        return {
            "passed": True,
            "match_type": "exact",
            "similarity": 1.0,
            "details": f"Found exact match for '{expected}' in response"
        }

    # Try fuzzy matching - check if any substring is similar
    # Slide a window of expected length over the response
    best_ratio = 0.0
    best_match = ""

    words = response.split()
    expected_words = expected.split()

    # For multi-word expected values, check word sequences
    for i in range(len(words) - len(expected_words) + 1):
        window = " ".join(words[i:i + len(expected_words)])
        ratio = SequenceMatcher(None, window.lower(), expected_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = window

    # Also check the full response similarity
    full_ratio = SequenceMatcher(None, response_lower, expected_lower).ratio()
    if full_ratio > best_ratio:
        best_ratio = full_ratio
        best_match = response

    passed = best_ratio >= fuzzy_threshold

    return {
        "passed": passed,
        "match_type": "fuzzy" if passed else "no_match",
        "similarity": best_ratio,
        "details": f"Best match: '{best_match}' with similarity {best_ratio:.2%}"
    }


def evaluate_llm_judge(
    question: str,
    response: str,
    expected: str,
    client: anthropic.Anthropic | None = None
) -> dict:
    """Use Claude as a judge to evaluate semantic correctness.

    Args:
        question: The original question asked
        response: The model's response
        expected: The expected answer or key points
        client: Anthropic client (creates one if not provided)

    Returns:
        dict with 'passed', 'score', 'reasoning', and 'details'
    """
    if client is None:
        client = anthropic.Anthropic()

    judge_prompt = f"""You are evaluating whether an AI assistant's response correctly answers a question about NIH research grants.

QUESTION: {question}

EXPECTED ANSWER/KEY POINTS: {expected}

ACTUAL RESPONSE: {response}

Evaluate whether the actual response correctly captures the key information from the expected answer. The response doesn't need to be word-for-word identical, but should convey the same essential information.

Provide your evaluation in the following format:
SCORE: [0-10] (0 = completely wrong, 10 = perfectly correct)
REASONING: [Your explanation of why you gave this score]
VERDICT: [PASS or FAIL] (PASS if score >= 7)"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[
            {"role": "user", "content": judge_prompt}
        ]
    )

    judge_response = message.content[0].text

    # Parse the judge's response
    score = 0
    reasoning = ""
    verdict = "FAIL"

    for line in judge_response.split("\n"):
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                score = int(re.search(r"\d+", line).group())
            except (AttributeError, ValueError):
                score = 0
        elif line.startswith("REASONING:"):
            reasoning = line[10:].strip()
        elif line.startswith("VERDICT:"):
            verdict = "PASS" if "PASS" in line.upper() else "FAIL"

    return {
        "passed": verdict == "PASS",
        "score": score,
        "reasoning": reasoning,
        "details": judge_response
    }
