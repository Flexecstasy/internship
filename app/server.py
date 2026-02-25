import json
import re
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .db import get_conn, init_db

BASE = Path(__file__).resolve().parent
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def json_response(start_response, status_code: int, payload: dict | list):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    statuses = {200: "200 OK", 201: "201 Created", 400: "400 Bad Request", 404: "404 Not Found", 422: "422 Unprocessable Entity", 500: "500 Internal Server Error"}
    start_response(statuses[status_code], [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


def read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length) if length > 0 else b"{}"
    return json.loads(raw.decode("utf-8"))


def error(status_code: int, error_code: str, user_message: str, developer_message: str, suggestion: str, details=None):
    return {
        "status_code": status_code,
        "payload": {
            "error_code": error_code,
            "user_message": user_message,
            "developer_message": developer_message,
            "suggestion": suggestion,
            "details": details or {},
        },
    }


def get_vacancies():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT v.id, v.title, v.description, v.status, v.salary_per_hour, v.workload_hours,
               e.name AS employer, d.name AS department, l.campus_zone, l.room
        FROM vacancies v
        JOIN employers e ON e.id = v.employer_id
        JOIN departments d ON d.id = v.department_id
        JOIN locations l ON l.id = v.location_id
        ORDER BY v.id
        """
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "status": r["status"],
            "salary_per_hour": r["salary_per_hour"],
            "workload_hours": r["workload_hours"],
            "employer": r["employer"],
            "department": r["department"],
            "location": f"{r['campus_zone']}, {r['room']}",
        }
        for r in rows
    ]


def validate_payload(payload):
    field_errors = []
    if not EMAIL_RE.match(payload.get("student_email", "")):
        field_errors.append({"field": "student_email", "issue": "Некорректный email"})
    if len(payload.get("student_full_name", "")) < 3:
        field_errors.append({"field": "student_full_name", "issue": "Минимум 3 символа"})
    if len(payload.get("faculty", "")) < 2:
        field_errors.append({"field": "faculty", "issue": "Минимум 2 символа"})
    year = payload.get("study_year")
    if not isinstance(year, int) or not 1 <= year <= 6:
        field_errors.append({"field": "study_year", "issue": "Допустимо значение от 1 до 6"})
    if len(payload.get("cover_letter", "")) < 30:
        field_errors.append({"field": "cover_letter", "issue": "Минимум 30 символов"})
    return field_errors


def app(environ, start_response):
    try:
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")

        if path == "/" and method == "GET":
            file = (BASE / "templates" / "index.html").read_bytes()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(file)))])
            return [file]

        if path.startswith("/static/") and method == "GET":
            file_path = BASE / path.lstrip("/")
            if not file_path.exists():
                return json_response(start_response, 404, {"message": "Not found"})
            content_type = "text/plain"
            if file_path.suffix == ".css":
                content_type = "text/css"
            elif file_path.suffix == ".js":
                content_type = "application/javascript"
            file = file_path.read_bytes()
            start_response("200 OK", [("Content-Type", f"{content_type}; charset=utf-8"), ("Content-Length", str(len(file)))])
            return [file]

        if path == "/docs" and method == "GET":
            docs = (BASE / "templates" / "docs.html").read_bytes()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(docs)))])
            return [docs]

        if path == "/api/health" and method == "GET":
            return json_response(start_response, 200, {"status": "ok"})

        if path == "/api/vacancies" and method == "GET":
            return json_response(start_response, 200, get_vacancies())

        if path.startswith("/api/vacancies/") and method == "GET":
            vacancy_id = path.split("/")[-1]
            if not vacancy_id.isdigit():
                err = error(400, "INVALID_VACANCY_ID", "Некорректный идентификатор вакансии.", "vacancy_id must be numeric.", "Используйте id из /api/vacancies")
                return json_response(start_response, err["status_code"], err["payload"])
            item = next((v for v in get_vacancies() if v["id"] == int(vacancy_id)), None)
            if not item:
                err = error(404, "VACANCY_NOT_FOUND", "Вакансия не найдена.", f"Vacancy id={vacancy_id} not found.", "Обновите список вакансий.", {"vacancy_id": int(vacancy_id)})
                return json_response(start_response, err["status_code"], err["payload"])
            return json_response(start_response, 200, item)

        if path.startswith("/api/vacancies/") and path.endswith("/apply") and method == "POST":
            vacancy_id = path.split("/")[-2]
            if not vacancy_id.isdigit():
                err = error(400, "INVALID_VACANCY_ID", "Некорректный идентификатор вакансии.", "vacancy_id must be numeric.", "Используйте id из /api/vacancies")
                return json_response(start_response, err["status_code"], err["payload"])
            payload = read_json(environ)
            field_errors = validate_payload(payload)
            if field_errors:
                err = error(422, "VALIDATION_ERROR", "Некоторые поля заполнены неверно.", "Request body validation failed.", "Проверьте формат полей в API docs.", {"fields": field_errors})
                return json_response(start_response, err["status_code"], err["payload"])

            vacancies = get_vacancies()
            if not any(v["id"] == int(vacancy_id) for v in vacancies):
                err = error(404, "VACANCY_NOT_FOUND", "Нельзя отправить отклик: вакансия не найдена.", f"Vacancy id={vacancy_id} not found.", "Выберите актуальную вакансию.", {"vacancy_id": int(vacancy_id)})
                return json_response(start_response, err["status_code"], err["payload"])

            conn = get_conn()
            cur = conn.cursor()
            student = cur.execute("SELECT * FROM students WHERE email = ?", (payload["student_email"],)).fetchone()
            if not student:
                cur.execute(
                    "INSERT INTO students(full_name, email, faculty, study_year) VALUES (?, ?, ?, ?)",
                    (payload["student_full_name"], payload["student_email"], payload["faculty"], payload["study_year"]),
                )
                student_id = cur.lastrowid
            else:
                student_id = student["id"]

            duplicate = cur.execute(
                "SELECT id FROM applications WHERE student_id = ? AND vacancy_id = ?",
                (student_id, int(vacancy_id)),
            ).fetchone()
            if duplicate:
                conn.close()
                err = error(400, "DUPLICATE_APPLICATION", "Вы уже отправили отклик на эту вакансию.", "Duplicate application business constraint.", "Проверьте статус в разделе «Мои отклики».", {"application_id": duplicate["id"]})
                return json_response(start_response, err["status_code"], err["payload"])

            cur.execute(
                "INSERT INTO applications(student_id, vacancy_id, status, cover_letter) VALUES (?, ?, ?, ?)",
                (student_id, int(vacancy_id), "submitted", payload["cover_letter"]),
            )
            app_id = cur.lastrowid
            conn.commit()
            created = cur.execute("SELECT created_at FROM applications WHERE id = ?", (app_id,)).fetchone()["created_at"]
            vacancy_title = cur.execute("SELECT title FROM vacancies WHERE id = ?", (int(vacancy_id),)).fetchone()["title"]
            conn.close()
            return json_response(start_response, 201, {"id": app_id, "vacancy_id": int(vacancy_id), "vacancy_title": vacancy_title, "student_email": payload["student_email"], "status": "submitted", "created_at": created})

        if path == "/api/applications" and method == "GET":
            qs = parse_qs(environ.get("QUERY_STRING", ""))
            student_email = (qs.get("student_email") or [""])[0]
            conn = get_conn()
            student = conn.execute("SELECT id FROM students WHERE email = ?", (student_email,)).fetchone()
            if not student:
                conn.close()
                err = error(404, "STUDENT_NOT_FOUND", "Студент с таким email не найден.", f"Student email={student_email} not found.", "Проверьте email или сначала отправьте отклик.", {"student_email": student_email})
                return json_response(start_response, err["status_code"], err["payload"])
            rows = conn.execute(
                """
                SELECT a.id, a.vacancy_id, a.status, a.created_at, v.title
                FROM applications a JOIN vacancies v ON v.id = a.vacancy_id
                WHERE a.student_id = ?
                ORDER BY a.id DESC
                """,
                (student["id"],),
            ).fetchall()
            conn.close()
            data = [{"id": r["id"], "vacancy_id": r["vacancy_id"], "vacancy_title": r["title"], "student_email": student_email, "status": r["status"], "created_at": r["created_at"]} for r in rows]
            return json_response(start_response, 200, data)

        return json_response(start_response, 404, {"message": "Not found"})
    except Exception as exc:
        err = error(500, "INTERNAL_SERVER_ERROR", "На сервере произошла ошибка.", str(exc), "Повторите попытку позже.")
        return json_response(start_response, err["status_code"], err["payload"])


def run(host="127.0.0.1", port=8000):
    init_db()
    with make_server(host, port, app) as server:
        print(f"Serving on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    run()
