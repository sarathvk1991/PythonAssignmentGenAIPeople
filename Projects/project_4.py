"""Script to read a specific page from a PDF in the Content folder,
filter it using a regex from a config file, and write matches to output.txt."""

from pathlib import Path
import json
import re

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
    configs_dir = Path(__file__).parent.parent / "Configs"
    
    # 1. Handle case where folder is not available
    if not content_dir.exists():
        print(f"Error: Content folder not found: {content_dir}")
        return

    if not content_dir.is_dir():
        print(f"Error: {content_dir} is not a directory.")
        return

    # 4. Handle case where no configuration file is available
    config_path = configs_dir / "config.json"
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return

    # Load configuration
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse configuration file: {e}")
        return
    except OSError as e:
        print(f"Error: Failed to read configuration file: {e}")
        return

    # 5. Handle the case where configuration file does not have the regular expression
    regex_pattern = config.get("regex")
    if not regex_pattern:
        print("Error: Configuration file does not contain a 'regex' key or it is empty.")
        return

    # Compile regex and handle invalid patterns
    try:
        pattern = re.compile(regex_pattern, re.MULTILINE)
    except re.error as e:
        print(f"Error: Invalid regular expression in configuration: {e}")
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
    # 3. Update code to extract only the content matching the regular expression
    matches = pattern.findall(text)
    if not matches:
        print("No content matched the configured regular expression.")
        write_text_to_output("")
        return

    formatted_matches = []

    for m in matches:
        if isinstance(m, tuple):
            formatted_matches.append("\n".join(part.strip() for part in m if part))
        else:
            formatted_matches.append(str(m).strip())

    matched_text = "\n\n".join(formatted_matches)
    write_text_to_output(matched_text)


if __name__ == "__main__":
    main()

