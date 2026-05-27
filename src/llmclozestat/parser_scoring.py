from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedFill:
    blank_id: str
    position: int
    extracted_fill: str | None
    fill_class: str
    blank_parse_pass: bool
    content_pass: bool
    parse_fail: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "blank_id": self.blank_id,
            "position": self.position,
            "extracted_fill": self.extracted_fill,
            "fill_class": self.fill_class,
            "blank_parse_pass": self.blank_parse_pass,
            "content_pass": self.content_pass,
            "parse_fail": self.parse_fail,
        }


def parse_and_score_item(
    item: dict[str, Any],
    raw_output: str,
    parser_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse and score one model output for one cloze item.

    This is the strict v0 parser/scorer core. It intentionally does not
    implement fallback answer extraction or LLM-based judging.
    """

    normalized_output = normalize_output(raw_output, parser_config or {})
    expected_full_texts = item.get("expected_full_texts", [])
    blanks = item.get("blanks", [])

    if normalized_output in expected_full_texts:
        extraction_mode = "exact_full_text"
        fills = extract_by_segments(item, normalized_output)
        extraction_success = fills is not None
    else:
        extraction_mode = "segment"
        fills = extract_by_segments(item, normalized_output)
        extraction_success = fills is not None

    if extraction_success and fills is not None:
        blank_results = [
            classify_blank(blank, fills.get(blank.get("blank_id", "")))
            for blank in blanks
            if isinstance(blank, dict)
        ]
    else:
        blank_results = [parse_fail_blank(blank) for blank in blanks if isinstance(blank, dict)]

    item_format_pass = bool(extraction_success)
    instruction_following_pass = item_format_pass
    accepted_count = sum(1 for result in blank_results if result.content_pass)
    blank_count = len(blank_results)
    item_partial_score = accepted_count / blank_count if blank_count else 0.0
    item_strict_pass = (
        instruction_following_pass
        and item_format_pass
        and bool(blank_results)
        and all(result.content_pass for result in blank_results)
    )

    return {
        "raw_output": raw_output,
        "normalized_output": normalized_output,
        "extraction_mode": extraction_mode,
        "blank_results": [result.to_dict() for result in blank_results],
        "instruction_following_pass": instruction_following_pass,
        "item_format_pass": item_format_pass,
        "item_partial_score": item_partial_score,
        "item_strict_pass": item_strict_pass,
    }


def normalize_output(raw_output: str, parser_config: dict[str, Any] | None = None) -> str:
    """Apply v0 minimal normalization."""
    del parser_config
    normalized = raw_output.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def extract_by_segments(item: dict[str, Any], normalized_output: str) -> dict[str, str] | None:
    segments = item.get("segments")
    blanks = item.get("blanks")
    if not isinstance(segments, list) or not isinstance(blanks, list):
        return None
    if len(segments) != len(blanks) + 1:
        return None
    if not all(isinstance(segment, str) for segment in segments):
        return None

    cursor = 0
    first_segment = segments[0]
    if first_segment:
        start = normalized_output.find(first_segment, cursor)
        if start != cursor:
            return None
        cursor = start + len(first_segment)

    fills: dict[str, str] = {}
    for index, blank in enumerate(blanks):
        if not isinstance(blank, dict):
            return None
        next_segment = segments[index + 1]
        if next_segment:
            next_index = normalized_output.find(next_segment, cursor)
            if next_index < 0:
                return None
            fill = normalized_output[cursor:next_index]
            cursor = next_index + len(next_segment)
        else:
            fill = normalized_output[cursor:]
            cursor = len(normalized_output)
        blank_id = blank.get("blank_id")
        if not isinstance(blank_id, str):
            return None
        fills[blank_id] = fill

    if cursor != len(normalized_output):
        return None
    return fills


def classify_blank(blank: dict[str, Any], extracted_fill: str | None) -> ParsedFill:
    blank_id = str(blank.get("blank_id", ""))
    position = int(blank.get("position", 0))
    if extracted_fill is None:
        return parse_fail_blank(blank)

    fill_class = classify_fill(blank, extracted_fill)
    content_pass = fill_class == "accepted"
    return ParsedFill(
        blank_id=blank_id,
        position=position,
        extracted_fill=extracted_fill,
        fill_class=fill_class,
        blank_parse_pass=True,
        content_pass=content_pass,
        parse_fail=False,
    )


def classify_fill(blank: dict[str, Any], extracted_fill: str) -> str:
    if extracted_fill in blank.get("accepted_fills", []):
        return "accepted"
    if extracted_fill in blank.get("near_miss_fills", []):
        return "near_miss"
    if extracted_fill in blank.get("known_wrong_fills", []):
        return "known_wrong"
    return "wrong"


def parse_fail_blank(blank: dict[str, Any]) -> ParsedFill:
    return ParsedFill(
        blank_id=str(blank.get("blank_id", "")),
        position=int(blank.get("position", 0)),
        extracted_fill=None,
        fill_class="parse_fail",
        blank_parse_pass=False,
        content_pass=False,
        parse_fail=True,
    )
