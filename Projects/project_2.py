"""Process PDF files in Content sub-folders and write content to output.txt in each."""

from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Please install pypdf: pip install pypdf")
    raise SystemExit(1)


def read_pdf(pdf_path: Path) -> str:
    """Read and extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def process_content_folder() -> None:
    """Load PDFs from each Content sub-folder and write to output.txt."""
    content_dir = Path(__file__).parent.parent / "Content"

    # 1. Handle case where Content folder is not available
    if not content_dir.exists():
        print(f"Error: Content folder not found at {content_dir}")
        return

    if not content_dir.is_dir():
        print(f"Error: {content_dir} is not a directory.")
        return

    subfolders = [f for f in content_dir.iterdir() if f.is_dir()]

    if not subfolders:
        print("No sub-folders found under Content directory.")
        return

    for subfolder in sorted(subfolders):
        print(f"\nProcessing sub-folder: {subfolder.name}")

        # 2. Handle case where PDF file is not present in a sub-folder
        pdf_files = list(subfolder.glob("*.pdf"))
        if not pdf_files:
            print(f"  Skipping: No PDF files found in {subfolder.name}")
            continue

        # Extract text from all PDFs in the sub-folder
        combined_text = []
        for pdf_path in sorted(pdf_files):
            try:
                text = read_pdf(pdf_path)
                combined_text.append(f"--- {pdf_path.name} ---\n{text}")
            except Exception as e:
                print(f"  Error reading {pdf_path.name}: {e}")
                continue

        if not combined_text:
            print(f"  Skipping: Could not extract text from any PDF in {subfolder.name}")
            continue

        # 3. Handle case where output.txt cannot be written
        output_path = subfolder / "output.txt"
        try:
            output_path.write_text("\n\n".join(combined_text), encoding="utf-8")
            print(f"  Success: Written to {output_path}")
        except PermissionError:
            print(f"  Error: Cannot write to {output_path} (permission denied)")
        except OSError as e:
            print(f"  Error: Failed to write output.txt in {subfolder.name}: {e}")


if __name__ == "__main__":
    process_content_folder()
