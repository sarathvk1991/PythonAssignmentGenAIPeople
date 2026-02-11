"""Script to load an RSS XML file, fetch each linked page in parallel,
and write the fetched content to output.txt."""

from __future__ import annotations

from pathlib import Path
import concurrent.futures
import xml.etree.ElementTree as ET

import requests


def fetch_url(url: str, timeout: float = 10.0) -> str:
    """Fetch the content of a URL, returning an empty string on error."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:  # noqa: BLE001
        print(f"Error fetching {url}: {e}")
        return ""


def main() -> None:
    root_dir = Path(__file__).parent.parent
    content_dir = root_dir / "Content"
    rss_path = content_dir / "sample_rss.xml"

    # 1. Take care of case where no RSS xml file is available
    if not rss_path.exists():
        print(f"Error: RSS XML file not found at {rss_path}")
        return

    # Read XML file
    try:
        xml_text = rss_path.read_text(encoding="utf-8").strip()
    except OSError as e:
        print(f"Error reading RSS XML file: {e}")
        return

    # 2. Take care of case where xml file is empty
    if not xml_text:
        print("Error: RSS XML file is empty.")
        return

    # Parse XML
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"Error: Failed to parse RSS XML file: {e}")
        return

    # 2. Loop through each link (all <link> elements in the RSS)
    links: list[str] = []
    for link_elem in root.iter("link"):
        text = (link_elem.text or "").strip()
        if text:
            links.append(text)

    if not links:
        print("No <link> elements found in RSS XML.")
        return

    print(f"Found {len(links)} link(s) in RSS. Fetching in parallel...")

    # 4. Execute reading from multiple links in parallel
    fetched_contents: list[tuple[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in links}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                content = future.result()
            except Exception as e:  # noqa: BLE001
                print(f"Unexpected error fetching {url}: {e}")
                content = ""

            if content:
                fetched_contents.append((url, content))

    # 3. Extract content from each link and write to “output.txt”
    output_path = content_dir / "output.txt"
    try:
        if not fetched_contents:
            output_text = "No content could be fetched from any link.\n"
        else:
            parts: list[str] = []
            for url, content in fetched_contents:
                parts.append(f"URL: {url}\n{'=' * 80}\n{content}\n")
            output_text = "\n".join(parts)

        output_path.write_text(output_text, encoding="utf-8")
        print(f"Wrote fetched content from {len(fetched_contents)} link(s) to {output_path}")
    except OSError as e:
        print(f"Error writing to output file {output_path}: {e}")


if __name__ == "__main__":
    main()

