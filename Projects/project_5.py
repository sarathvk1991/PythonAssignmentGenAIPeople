"""Script to load questions from a PDF using a regex from config.json
and store them in a MySQL database.

DB connection settings are read from `Configs/config.json` under the `db` key.
"""

from pathlib import Path
import json
import re

try:
    from pypdf import PdfReader
except ImportError:
    print("Please install pypdf: pip install pypdf")
    raise SystemExit(1)

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("Please install mysql-connector-python: pip install mysql-connector-python")
    raise SystemExit(1)


def get_db_connection(db_config: dict) -> mysql.connector.MySQLConnection | None:
    """Create and return a MySQL connection, handling 'database not available'."""
    try:
        conn = mysql.connector.connect(
            host=db_config.get("host", "localhost"),
            port=int(db_config.get("port", 3306)),
            user=db_config.get("user"),
            password=db_config.get("password"),
            database=db_config.get("database"),
        )
        if not conn.is_connected():
            print("Error: Database not available (connection not established).")
            return None
        return conn
    except (MySQLError, ValueError, TypeError) as e:
        print(f"Error: Database not available ({e}).")
        return None


def ensure_question_table(conn: mysql.connector.MySQLConnection) -> bool:
    """Ensure the Question table exists."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS Question (
        id BIGINT NOT NULL AUTO_INCREMENT,
        subject_name VARCHAR(255) NULL,
        question_text TEXT NOT NULL,
        answer_options TEXT NULL,
        chapter_name VARCHAR(255) NULL,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        cur = conn.cursor()
        cur.execute(create_sql)
        conn.commit()
        cur.close()
        return True
    except MySQLError as e:
        print(f"Error: Question table is not available or could not be created ({e}).")
        return False


def insert_question(
    conn: mysql.connector.MySQLConnection,
    subject_name: str,
    question_text: str,
    answer_options: str,
    chapter_name: str,
) -> None:
    """Insert a single question row, handling DB operation errors."""
    sql = """
    INSERT INTO Question (subject_name, question_text, answer_options, chapter_name)
    VALUES (%s, %s, %s, %s);
    """
    try:
        cur = conn.cursor()
        cur.execute(sql, (subject_name, question_text, answer_options, chapter_name))
        conn.commit()
        cur.close()
    except MySQLError as e:
        print(f"Error inserting question into database: {e}")


def main():
    root_dir = Path(__file__).parent.parent
    content_dir = root_dir / "Content"
    configs_dir = root_dir / "Configs"

    if not content_dir.exists():
        print(f"Error: Content folder not found: {content_dir}")
        return

    if not content_dir.is_dir():
        print(f"Error: {content_dir} is not a directory.")
        return

    config_path = configs_dir / "config.json"
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse configuration file: {e}")
        return
    except OSError as e:
        print(f"Error: Failed to read configuration file: {e}")
        return

    regex_pattern = config.get("regex")
    chapter_regex = config.get("chapter_regex")

    if not regex_pattern or not chapter_regex:
        print("Error: Configuration must contain 'regex' and 'chapter_regex'.")
        return

    try:
        question_pattern = re.compile(regex_pattern, re.DOTALL)
        chapter_pattern = re.compile(chapter_regex, re.MULTILINE)
    except re.error as e:
        print(f"Error: Invalid regular expression in configuration: {e}")
        return

    db_config = config.get("db")
    if not isinstance(db_config, dict):
        print("Error: Configuration file does not contain valid 'db' settings.")
        return

    conn = get_db_connection(db_config)
    if conn is None:
        return

    if not ensure_question_table(conn):
        conn.close()
        return

    pdf_files = list(content_dir.glob("Chemistry Questions.pdf"))
    if not pdf_files:
        print("Error: No PDF files found in Content folder.")
        conn.close()
        return

    pdf_path = pdf_files[0]
    print(f"\nLoading questions from: {pdf_path.name}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"Error opening PDF file {pdf_path.name}: {e}")
        conn.close()
        return

    full_text_parts: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
            full_text_parts.append(page_text)
        except Exception as e:
            print(f"Warning: Error reading page {page_index}: {e}")

    full_text = "\n".join(full_text_parts)

    default_subject = config.get("subject_name", "Unknown Subject")
    stored_count = 0

    # Chapter-wise parsing
    for chap_match in chapter_pattern.finditer(full_text):
        chapter_start = chap_match.start()
        chapter_name = chap_match.group("chapter").strip()

        next_chap = chapter_pattern.search(full_text, chap_match.end())
        chapter_end = next_chap.start() if next_chap else len(full_text)

        chapter_text = full_text[chapter_start:chapter_end]

        for match in question_pattern.finditer(chapter_text):
            question_text = match.group("question").strip()
            options = match.group("options").strip()

            insert_question(
                conn=conn,
                subject_name=default_subject,
                question_text=question_text,
                answer_options=options,
                chapter_name=chapter_name,
            )
            stored_count += 1

    print(f"Stored {stored_count} question(s) in the MySQL database '{db_config.get('database')}'.")
    conn.close()


if __name__ == "__main__":
    main()
