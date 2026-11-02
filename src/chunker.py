
import re


def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Divide text into overlapping chunks.

    Args:
        text: Extracted text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of repeated characters.

    Returns:
        List of text chunks.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks = []

    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# Detect common research paper section headings
SECTION_PATTERN = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?"
    r"(abstract|introduction|background|related work|"
    r"literature review|methodology|methods|proposed method|"
    r"experiments|experimental setup|results|discussion|"
    r"limitations|conclusion|conclusions|future work|references)\s*$",
    re.IGNORECASE
)


def find_section_headings_with_offsets(text):
    """
    Find all section headings and their character start offsets in text.
    Handles:
    - Single-line numbered or unnumbered headings (e.g. '1. Introduction', 'Conclusion')
    - Split-line headings where section number/prefix is on one line and heading title on the next (e.g. '7\\nConclusion')
    - Split-line multi-word headings across adjacent lines (e.g. 'Related\\nWork')
    """
    headings = []
    lines_with_offsets = []
    offset = 0

    for line in text.splitlines(keepends=True):
        lines_with_offsets.append((offset, line))
        offset += len(line)

    i = 0
    num_lines = len(lines_with_offsets)

    while i < num_lines:
        line_offset, line = lines_with_offsets[i]
        line_clean = line.strip()

        if not line_clean:
            i += 1
            continue

        # 1. Single-line heading match
        single_match = SECTION_PATTERN.match(line_clean)
        if single_match:
            sec_name = single_match.group(1).title()
            if sec_name.lower() == "conclusions":
                sec_name = "Conclusion"
            headings.append((line_offset, sec_name))
            i += 1
            continue

        # 2. Split-line heading match across adjacent lines
        if i + 1 < num_lines:
            next_offset, next_line = lines_with_offsets[i + 1]
            next_clean = next_line.strip()
            if next_clean:
                combined_two_lines = f"{line_clean} {next_clean}"
                two_line_match = SECTION_PATTERN.match(combined_two_lines)
                if two_line_match:
                    sec_name = two_line_match.group(1).title()
                    if sec_name.lower() == "conclusions":
                        sec_name = "Conclusion"
                    headings.append((line_offset, sec_name))
                    i += 2
                    continue

        i += 1

    return headings


def detect_section(text, current_section="Unknown"):
    """
    Detect the section heading from a line of text or text block.
    Preserves backward compatibility for callers and unit tests.
    """
    headings = find_section_headings_with_offsets(text)
    if headings:
        return headings[-1][1]
    return current_section


def chunk_pages(
    pages,
    paper_id,
    paper_title,
    chunk_size=1000,
    overlap=200
):
    """
    Chunk extracted PDF pages while preserving metadata with offset-aware section assignment.

    Args:
        pages: List of extracted page dictionaries.
        paper_id: Unique paper identifier.
        paper_title: Research paper title.
        chunk_size: Maximum characters per chunk.
        overlap: Overlapping characters.

    Returns:
        List of dictionaries containing chunk text and metadata.
    """

    all_chunks = []
    chunk_number = 1
    current_section = "Unknown"

    for page in pages:
        page_number = page["page"]
        page_text = page["text"]

        if not page_text.strip():
            continue

        # Find all headings with their exact start character offsets on this page
        page_headings = find_section_headings_with_offsets(page_text)

        start = 0
        text_len = len(page_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = page_text[start:end].strip()

            if chunk:
                # Active section is determined by the latest heading on this page
                # that appears at or before the chunk's midpoint
                midpoint = start + (end - start) // 2
                chunk_section = current_section

                for h_off, h_name in page_headings:
                    if h_off <= midpoint:
                        chunk_section = h_name

                chunk_data = {
                    "chunk_id": f"{paper_id}_C{chunk_number:04d}",
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "section": chunk_section,
                    "page_number": page_number,
                    "text": chunk
                }
                all_chunks.append(chunk_data)
                chunk_number += 1

            start += chunk_size - overlap

        # Carry forward the last detected section on this page to subsequent pages
        if page_headings:
            current_section = page_headings[-1][1]

    return all_chunks
