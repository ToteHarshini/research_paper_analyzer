
import re

SECTION_NAMES = [
    "abstract",
    "introduction",
    "related work",
    "background",
    "methodology",
    "methods",
    "experiments",
    "results",
    "limitations",
    "discussion",
    "conclusion",
    "references"
]


def detect_sections(text):

    sections = {}

    for section in SECTION_NAMES:

        pattern = rf"(?im)^\s*(?:\d+(?:\.\d+)*\.?\s*)?{re.escape(section)}\s*$"

        matches = list(re.finditer(pattern, text))

        if matches:
            sections[section] = matches[0].start()

    return sections
