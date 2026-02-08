"""Script to read PDF files from the Content folder."""

import os
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Please install pypdf: pip install pypdf")
    raise SystemExit(1)


def read_pdf(pdf_path: str | Path) -> str:
    """Read and extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)

#write the text to a file named output.txt in contents folder
def write_text_to_output(text: str):
    """Write the extracted text to output.txt in the Content folder."""
    output_path = Path(__file__).parent.parent / "Content" / "output.txt"
    with open(output_path, "w") as f:
        f.write(text)


def main():
    content_dir = Path(__file__).parent.parent / "Content"
    
    if not content_dir.exists():
        print(f"Content folder not found: {content_dir}")
        return
    
    pdf_files = list(content_dir.glob("Chemistry Questions.pdf"))
    
    if not pdf_files:
        print("No PDF files found in Content folder.")
        return
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"Reading: {pdf_path.name}")
        print("=" * 60)
        try:
            text = read_pdf(pdf_path)
            #print(text)
            write_text_to_output(text)
        except Exception as e:
            print(f"Error reading {pdf_path.name}: {e}")


if __name__ == "__main__":
    main()

