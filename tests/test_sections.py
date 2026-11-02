
from src.pdf_parser import extract_pdf_text
from src.section_extractor import detect_sections

pdf_path = "data/uploaded_pdfs/sample 2.pdf"


def main():
    # Extract PDF pages
    pages = extract_pdf_text(pdf_path)

    # Combine all pages into one text
    full_text = "\n".join(
        page["text"] for page in pages
    )

    # Detect sections
    sections = detect_sections(full_text)

    print("\n--- DETECTED SECTIONS ---")

    for section, position in sections.items():
        print(f"{section}: character position {position}")

    print("\nSection detection completed!")


if __name__ == "__main__":
    main()
