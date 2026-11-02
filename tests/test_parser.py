from src.pdf_parser import extract_pdf_text

pdf_path = "data/uploaded_pdfs/sample 2.pdf"


def main():
    print("Starting PDF parser test...")

    pages = extract_pdf_text(pdf_path)

    print("\n--- PDF PARSER TEST ---")

    print("Total pages:", len(pages))

    print("\n--- FIRST PAGE ---")
    print(pages[0]["text"])

    print("\n--- PAGE NUMBERS ---")
    for page in pages:
        print("Page:", page["page"])

    print("\nPDF parsing completed successfully!")


if __name__ == "__main__":
    main()