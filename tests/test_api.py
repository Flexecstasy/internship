import json
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from wsgiref.simple_server import make_server

from app.db import init_db
from app.server import app


BASE_URL = "http://127.0.0.1:8010"


def _start_server():
    init_db()
    server = make_server("127.0.0.1", 8010, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    return server


def _get(path):
    with urlopen(f"{BASE_URL}{path}") as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def test_key_flow_and_errors():
    server = _start_server()
    try:
        status, health = _get("/api/health")
        assert status == 200 and health["status"] == "ok"

        status, vacancies = _get("/api/vacancies")
        assert status == 200 and len(vacancies) >= 1
        vacancy_id = vacancies[0]["id"]

        bad_status, bad = _post(
            f"/api/vacancies/{vacancy_id}/apply",
            {
                "student_email": "bad",
                "student_full_name": "A",
                "faculty": "X",
                "study_year": 9,
                "cover_letter": "short",
            },
        )
        assert bad_status == 422
        assert bad["error_code"] == "VALIDATION_ERROR"

        payload = {
            "student_email": "student1@uni.local",
            "student_full_name": "Иван Иванов",
            "faculty": "ФКН",
            "study_year": 3,
            "cover_letter": "Очень хочу пройти стажировку и готов работать с Python и API каждый день.",
        }
        ok_status, ok_body = _post(f"/api/vacancies/{vacancy_id}/apply", payload)
        assert ok_status == 201
        assert ok_body["status"] == "submitted"

        dup_status, dup = _post(f"/api/vacancies/{vacancy_id}/apply", payload)
        assert dup_status == 400
        assert dup["error_code"] == "DUPLICATE_APPLICATION"

        status, apps = _get("/api/applications?student_email=student1@uni.local")
        assert status == 200 and len(apps) >= 1
    finally:
        server.shutdown()
