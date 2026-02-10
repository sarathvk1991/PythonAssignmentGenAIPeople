"""Script to read a specific page from a PDF in the Content folder."""

from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Please install pypdf: pip install pypdf")
    raise SystemExit(1)


def write_text_to_output(text: str) -> None:
    """Write the extracted text to output.txt in the Content folder."""
    output_path = Path(__file__).parent.parent / "Content" / "output.txt"
    try:
        # This will create output.txt if it does not exist
        output_path.write_text(text, encoding="utf-8")
        print(f"Output written to: {output_path}")
    except PermissionError:
        print(f"Error: Cannot write to {output_path} (permission denied)")
    except OSError as e:
        print(f"Error: Failed to write to {output_path}: {e}")


def main():
    content_dir = Path(__file__).parent.parent / "Content"
    
    # 1. Handle case where folder is not available
    if not content_dir.exists():
        print(f"Error: Content folder not found: {content_dir}")
        return

    if not content_dir.is_dir():
        print(f"Error: {content_dir} is not a directory.")
        return
    
    # Take page number as input from the command prompt
    try:
        page_input = input("Enter the page number to extract (starting from 1): ").strip()
        page_number = int(page_input)
        if page_number < 1:
            raise ValueError("Page number must be 1 or greater.")
    except ValueError as e:
        print(f"Invalid page number: {e}")
        return

    # 2. Handle case where PDF file is not present in the folder
    pdf_files = list(content_dir.glob("Chemistry Questions.pdf"))
    
    if not pdf_files:
        print("Error: No PDF files found in Content folder.")
        return
    
    # Use the first matching PDF file
    pdf_path = pdf_files[0]
    print(f"\nReading from file: {pdf_path.name}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"Error opening PDF file {pdf_path.name}: {e}")
        return

    total_pages = len(reader.pages)
    if page_number > total_pages:
        print(f"Error: Page number {page_number} is out of range. PDF has only {total_pages} pages.")
        return

    try:
        page = reader.pages[page_number - 1]
        text = page.extract_text() or ""
    except Exception as e:
        print(f"Error reading page {page_number} from {pdf_path.name}: {e}")
        return

    # 3. Handle case where output.txt file is not available in the folder
    # (we create it if missing, and handle write errors)
    write_text_to_output(text)


if __name__ == "__main__":
    main()

