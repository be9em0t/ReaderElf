"""Minimal text cleaning utilities for Reader Elf MVP."""
import re


def remove_headers_footers(text: str) -> str:
    # Very small heuristic: drop lines that look like page numbers or all-caps headers
    lines = text.splitlines()
    filtered = []
    for ln in lines:
        s = ln.strip()
        if not s:
            filtered.append(ln)
            continue
        # page numbers like "Page 12" or just numbers on a line
        if re.fullmatch(r'(page\s+\d+)|\d{1,4}', s.lower()):
            continue
        # all-caps short headers (<=5 words)
        if s.isupper() and len(s.split()) <= 6:
            continue
        filtered.append(ln)
    return "\n".join(filtered)


def fix_hyphenation(text: str) -> str:
    # remove hyphenation at line breaks: e.g. "impor-\ntant" -> "important"
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # remove linebreaks within paragraphs (heuristic: lines ending without punctuation)
    text = re.sub(r"(?<![\.\!\?;:\"\'])\n", " ", text)
    return text


def collapse_whitespace(text: str) -> str:
    return re.sub(r"[ \t\u00A0]+", " ", text).strip()


def clean_text(text: str) -> str:
    """Run a set of lightweight cleaning heuristics on input text."""
    t = text
    t = remove_headers_footers(t)
    t = fix_hyphenation(t)
    t = collapse_whitespace(t)
    return t


def split_notes(text: str):
    """Split out a trailing or embedded 'notes' / guidance section from text.

    Recognizes headings like: Edge cases, Notes, Next steps, Next steps & polishing,
    Edge cases and next improvements (case-insensitive). Returns a tuple
    (main_text, notes_text). If no notes heading is found, notes_text is empty.
    """
    # pattern matches lines starting with common guidance headings
    pattern = re.compile(r'(?im)^\s*(edge cases|notes|next steps|next steps & polishing|edge cases and next improvements).*$')
    m = pattern.search(text)
    if not m:
        return text, ''

    idx = m.start()

    # Heuristics to avoid false positives:
    # - If there's substantial (long) paragraph text before the heading, treat the
    #   match as part of the document and do not split.
    # - Otherwise, if the heading appears near the start of the document (first
    #   ~2000 chars or within the first 20 lines), consider it a notes section.

    before = text[:idx]
    # split by blank-line paragraphs and see if any paragraph is long enough
    paragraphs = re.split(r"\n{2,}", before)
    has_long_par = any(len(p.strip()) >= 80 for p in paragraphs)
    if has_long_par:
        # probably real document content before the heading — do not split
        return text, ''

    # count lines before match
    lines_before = before.count('\n')
    if idx <= 2000 or lines_before <= 20:
        main = before.rstrip('\n')
        notes = text[idx:].lstrip('\n')
        return main, notes

    # fallback: don't split
    return text, ''


if __name__ == "__main__":
    sample = """
    THIS IS A HEADER
    Page 1
    This is an impor-\ntant line.

    Another paragraph.
    """
    print(clean_text(sample))
