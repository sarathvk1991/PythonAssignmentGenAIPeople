"""Script to store different types of questions in a MySQL database using OOP concepts.

Supports:
1. Subjective questions (long answers)
2. Objective True/False questions
3. Objective multiple choice questions

Uses an interface (abstract base class) with inheritance for different question types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import json

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("Please install mysql-connector-python: pip install mysql-connector-python")
    raise SystemExit(1)


# Interface (Abstract Base Class) for Question
class Question(ABC):
    """Abstract base class defining the interface for all question types."""

    def __init__(self, question_text: str, subject_name: str = "", chapter_name: str = ""):
        """Initialize a question with common attributes."""
        self.question_text = question_text
        self.subject_name = subject_name
        self.chapter_name = chapter_name

    @abstractmethod
    def get_question_type(self) -> str:
        """Return the type of question."""
        pass

    @abstractmethod
    def get_answer_options(self) -> str:
        """Return the answer options as a formatted string."""
        pass

    @abstractmethod
    def store(self, conn: mysql.connector.MySQLConnection) -> bool:
        """Store the question in the database. Returns True on success, False on failure."""
        pass


# Concrete implementation: Subjective Question (Long Answer)
class SubjectiveQuestion(Question):
    """Subjective type question requiring a long answer."""

    def __init__(self, question_text: str, subject_name: str = "", chapter_name: str = ""):
        """Initialize a subjective question."""
        super().__init__(question_text, subject_name, chapter_name)

    def get_question_type(self) -> str:
        """Return the question type."""
        return "SUBJECTIVE"

    def get_answer_options(self) -> str:
        """Subjective questions don't have predefined options."""
        return ""

    def store(self, conn: mysql.connector.MySQLConnection) -> bool:
        """Store the subjective question in the database."""
        sql = """
        INSERT INTO Question_New (question_type, question_text, answer_options, subject_name, chapter_name)
        VALUES (%s, %s, %s, %s, %s);
        """
        try:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    self.get_question_type(),
                    self.question_text,
                    self.get_answer_options(),
                    self.subject_name,
                    self.chapter_name,
                ),
            )
            conn.commit()
            cur.close()
            return True
        except MySQLError as e:
            print(f"Error storing subjective question in database: {e}")
            return False


# Concrete implementation: True/False Question
class TrueFalseQuestion(Question):
    """Objective type question with True/False answer options."""

    def __init__(self, question_text: str, subject_name: str = "", chapter_name: str = ""):
        """Initialize a True/False question."""
        super().__init__(question_text, subject_name, chapter_name)

    def get_question_type(self) -> str:
        """Return the question type."""
        return "TRUE_FALSE"

    def get_answer_options(self) -> str:
        """Return True/False as the answer options."""
        return "True\nFalse"

    def store(self, conn: mysql.connector.MySQLConnection) -> bool:
        """Store the True/False question in the database."""
        sql = """
        INSERT INTO Question_New (question_type, question_text, answer_options, subject_name, chapter_name)
        VALUES (%s, %s, %s, %s, %s);
        """
        try:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    self.get_question_type(),
                    self.question_text,
                    self.get_answer_options(),
                    self.subject_name,
                    self.chapter_name,
                ),
            )
            conn.commit()
            cur.close()
            return True
        except MySQLError as e:
            print(f"Error storing True/False question in database: {e}")
            return False


# Concrete implementation: Multiple Choice Question
class MultipleChoiceQuestion(Question):
    """Objective type question with multiple answer choices."""

    def __init__(
        self,
        question_text: str,
        choices: list[str],
        subject_name: str = "",
        chapter_name: str = "",
    ):
        """Initialize a multiple choice question with a list of choices."""
        super().__init__(question_text, subject_name, chapter_name)
        self.choices = choices if choices else []

    def get_question_type(self) -> str:
        """Return the question type."""
        return "MULTIPLE_CHOICE"

    def get_answer_options(self) -> str:
        """Return the answer choices as a formatted string."""
        return "\n".join(self.choices)

    def store(self, conn: mysql.connector.MySQLConnection) -> bool:
        """Store the multiple choice question in the database."""
        sql = """
        INSERT INTO Question_New (question_type, question_text, answer_options, subject_name, chapter_name)
        VALUES (%s, %s, %s, %s, %s);
        """
        try:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    self.get_question_type(),
                    self.question_text,
                    self.get_answer_options(),
                    self.subject_name,
                    self.chapter_name,
                ),
            )
            conn.commit()
            cur.close()
            return True
        except MySQLError as e:
            print(f"Error storing multiple choice question in database: {e}")
            return False


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
    """Ensure the Question_New table exists with support for different question types."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS Question_New (
        id BIGINT NOT NULL AUTO_INCREMENT,
        question_type VARCHAR(50) NOT NULL,
        question_text TEXT NOT NULL,
        answer_options TEXT NULL,
        subject_name VARCHAR(255) NULL,
        chapter_name VARCHAR(255) NULL,
        PRIMARY KEY (id),
        INDEX idx_question_type (question_type)
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


def prompt_non_empty(prompt_text: str) -> str:
    """Prompt user until a non-empty string is entered."""
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("  Input cannot be empty. Please try again.")


def run_interactive_menu(conn: mysql.connector.MySQLConnection, default_subject: str, default_chapter: str) -> None:
    """Interactive interface: user selects question type, enters question, and stores in database."""
    while True:
        print("\n" + "=" * 50)
        print("  Question Management")
        print("=" * 50)
        print("  1. Add Subjective question (long answer)")
        print("  2. Add True/False question")
        print("  3. Add Multiple choice question")
        print("  4. Exit")
        print("=" * 50)

        choice = input("Select option (1-4): ").strip()

        if choice == "4":
            print("Goodbye.")
            break

        if choice not in ("1", "2", "3"):
            print("Invalid option. Please enter 1, 2, 3, or 4.")
            continue

        # Common inputs for all question types
        question_text = prompt_non_empty("Enter the question text: ")
        subject = input(f"Subject name [default: {default_subject}]: ").strip() or default_subject
        chapter = input(f"Chapter name [default: {default_chapter}]: ").strip() or default_chapter

        question: Question | None = None

        if choice == "1":
            question = SubjectiveQuestion(
                question_text=question_text,
                subject_name=subject,
                chapter_name=chapter,
            )
        elif choice == "2":
            question = TrueFalseQuestion(
                question_text=question_text,
                subject_name=subject,
                chapter_name=chapter,
            )
        elif choice == "3":
            print("Enter answer choices (one per line). Enter an empty line when done.")
            choices: list[str] = []
            while True:
                opt = input(f"  Choice {len(choices) + 1}: ").strip()
                if not opt:
                    if len(choices) < 2:
                        print("  Please enter at least 2 choices.")
                        continue
                    break
                choices.append(opt)
            question = MultipleChoiceQuestion(
                question_text=question_text,
                choices=choices,
                subject_name=subject,
                chapter_name=chapter,
            )

        if question and question.store(conn):
            print(f"Question stored successfully ({question.get_question_type()}).")
        elif question:
            print("Failed to store question. See error above.")


def main() -> None:
    """Main: load config, connect to DB, then run interactive interface."""
    root_dir = Path(__file__).parent.parent
    configs_dir = root_dir / "Configs"

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

    db_config = config.get("db")
    if not isinstance(db_config, dict):
        print("Error: Configuration file does not contain valid 'db' settings.")
        return

    conn = get_db_connection(db_config)
    if conn is None:
        return

    if not ensure_question_table(conn):
        try:
            conn.close()
        except Exception:
            pass
        return

    default_subject = config.get("subject_name", "General")
    default_chapter = config.get("chapter_name", "")

    print(f"Connected to database '{db_config.get('database')}'.")
    run_interactive_menu(conn, default_subject, default_chapter)

    try:
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
