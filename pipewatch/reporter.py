"""Formats and prints alert evaluation results to stdout."""

from __future__ import annotations

from typing import List

from pipewatch.evaluator import AlertEvent

ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_event(event: AlertEvent, use_color: bool = True) -> str:
    """Return a human-readable string for a single AlertEvent."""
    if event.triggered:
        color = ANSI_RED
        tag = "[ALERT]"
    else:
        color = ANSI_GREEN
        tag = "[OK]   "

    tag_str = _colorize(tag, color, use_color)
    return (
        f"{tag_str} {event.source_name}/{event.metric} = {event.value} "
        f"(threshold: {event.alert.operator} {event.alert.threshold})"
    )


def print_report(
    events: List[AlertEvent],
    use_color: bool = True,
    verbose: bool = False,
) -> int:
    """Print a report for all events.  Returns the number of triggered alerts."""
    triggered_count = 0

    if not events:
        label = _colorize("No alerts configured or no metrics fetched.", ANSI_YELLOW, use_color)
        print(label)
        return 0

    for event in events:
        if event.triggered or verbose:
            print(format_event(event, use_color=use_color))
        if event.triggered:
            triggered_count += 1

    summary_color = ANSI_RED if triggered_count else ANSI_GREEN
    summary = _colorize(
        f"\n{triggered_count}/{len(events)} alert(s) triggered.",
        summary_color,
        use_color,
    )
    print(summary)
    return triggered_count
