"""
Text cleaning service.

Normalizes whitespace and removes PDF extraction noise (broken line breaks,
repeated blank lines, stray page-number-only lines) without deleting
meaningful content.
"""
import re


def clean_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Join words that got hyphen-broken across a line wrap, e.g. "informa-\ntion"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Collapse a single newline that's really just a wrapped line (not a
    # paragraph break) into a space. We treat two-or-more newlines as an
    # intentional paragraph break and preserve it.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Collapse 3+ consecutive newlines down to a single paragraph break
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces/tabs
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Strip likely page-number-only lines, e.g. "12" or "Page 12" on their own line
    text = re.sub(r"(?im)^\s*(page\s+)?\d{1,4}\s*$", "", text)

    # Trim whitespace around lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line != "" or True)  # keep blank lines for paragraphing
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text
