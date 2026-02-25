import sqlite3
from pathlib import Path

DB_PATH = Path('internships.db')


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            faculty TEXT NOT NULL,
            study_year INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS employers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employer_type TEXT NOT NULL,
            contact_email TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            building TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vacancy_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campus_zone TEXT NOT NULL,
            room TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            salary_per_hour INTEGER NOT NULL,
            workload_hours INTEGER NOT NULL,
            employer_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vacancy_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            vacancy_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            cover_letter TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS application_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            old_status TEXT NOT NULL,
            new_status TEXT NOT NULL,
            changed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    vacancy_count = cur.execute("SELECT COUNT(*) AS c FROM vacancies").fetchone()["c"]
    if vacancy_count == 0:
        cur.execute("INSERT INTO employers(name, employer_type, contact_email) VALUES (?, ?, ?)", ("Кафедра ИТ", "department", "it-dept@uni.local"))
        employer_id = cur.lastrowid
        cur.execute("INSERT INTO departments(name, building) VALUES (?, ?)", ("Информационные технологии", "Корпус B"))
        department_id = cur.lastrowid
        cur.execute("INSERT INTO vacancy_categories(name) VALUES (?)", ("Стажировка",))
        category_id = cur.lastrowid
        cur.execute("INSERT INTO locations(campus_zone, room) VALUES (?, ?)", ("Северный кампус", "B-214"))
        location_id = cur.lastrowid
        cur.execute(
            "INSERT INTO vacancies(title, description, status, salary_per_hour, workload_hours, employer_id, department_id, category_id, location_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Стажер backend Python",
                "Помощь в разработке внутренних сервисов университета на Python.",
                "open",
                550,
                20,
                employer_id,
                department_id,
                category_id,
                location_id,
            ),
        )
        cur.execute(
            "INSERT INTO vacancies(title, description, status, salary_per_hour, workload_hours, employer_id, department_id, category_id, location_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Ассистент лаборатории данных",
                "Поддержка исследований и подготовка датасетов для научной группы.",
                "open",
                450,
                16,
                employer_id,
                department_id,
                category_id,
                location_id,
            ),
        )

    conn.commit()
    conn.close()
