
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
    r"limitations|conclusion|future work|references)\s*$",
    re.IGNORECASE
)


def detect_section(text, current_section="Unknown"):
    """
    Detect the section heading from a line of text.
    """

    for line in text.splitlines():

        match = SECTION_PATTERN.match(line)

        if match:
            current_section = match.group(1).title()

    return current_section


def chunk_pages(
    pages,
    paper_id,
    paper_title,
    chunk_size=1000,
    overlap=200
):
    """
    Chunk extracted PDF pages while preserving metadata.

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

        # Update section based on headings on this page
        current_section = detect_section(
            page_text,
            current_section
        )

        # Divide page text into smaller chunks
        text_chunks = chunk_text(
            page_text,
            chunk_size,
            overlap
        )

        for chunk in text_chunks:

            chunk_data = {
                "chunk_id": f"{paper_id}_C{chunk_number:04d}",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "section": current_section,
                "page_number": page_number,
                "text": chunk
            }

            all_chunks.append(chunk_data)

            chunk_number += 1

    return all_chunks
