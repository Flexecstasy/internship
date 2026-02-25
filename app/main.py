from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette import status

from .database import Base, SessionLocal, engine
from .errors import (
    ApiException,
    api_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from .models import (
    Application,
    Department,
    Employer,
    Location,
    Student,
    Vacancy,
    VacancyCategory,
)
from .schemas import ApplicationCreate, ApplicationOut, HealthOut, VacancyOut

app = FastAPI(
    title="Campus Jobs API",
    description="API для поиска временной работы и стажировок в университете.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_exception_handler(ApiException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


BASE_DIR = Path(__file__).resolve().parent


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data(db: Session) -> None:
    if db.query(Vacancy).count() > 0:
        return

    employer = Employer(name="Кафедра ИТ", employer_type="department", contact_email="it-dept@uni.local")
    department = Department(name="Информационные технологии", building="Корпус B")
    category = VacancyCategory(name="Стажировка")
    location = Location(campus_zone="Северный кампус", room="B-214")

    db.add_all([employer, department, category, location])
    db.flush()

    vacancies = [
        Vacancy(
            title="Стажер backend Python",
            description="Помощь в разработке внутренних сервисов университета на Python/FastAPI.",
            status="open",
            salary_per_hour=550,
            workload_hours=20,
            employer_id=employer.id,
            department_id=department.id,
            category_id=category.id,
            location_id=location.id,
        ),
        Vacancy(
            title="Ассистент лаборатории данных",
            description="Поддержка исследований и подготовка датасетов для научной группы.",
            status="open",
            salary_per_hour=450,
            workload_hours=16,
            employer_id=employer.id,
            department_id=department.id,
            category_id=category.id,
            location_id=location.id,
        ),
    ]
    db.add_all(vacancies)
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.get("/api/health", response_model=HealthOut)
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/vacancies", response_model=list[VacancyOut])
def list_vacancies(db: Session = Depends(get_db)) -> list[VacancyOut]:
    vacancies = db.query(Vacancy).all()
    return [
        VacancyOut(
            id=v.id,
            title=v.title,
            description=v.description,
            employer=v.employer.name,
            department=v.department.name,
            location=f"{v.location.campus_zone}, {v.location.room}",
            salary_per_hour=v.salary_per_hour,
            workload_hours=v.workload_hours,
            status=v.status,
        )
        for v in vacancies
    ]


@app.get("/api/vacancies/{vacancy_id}", response_model=VacancyOut)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)) -> VacancyOut:
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="VACANCY_NOT_FOUND",
            user_message="Вакансия не найдена.",
            developer_message=f"Vacancy with id={vacancy_id} does not exist.",
            suggestion="Проверьте идентификатор вакансии или обновите список вакансий.",
            details={"vacancy_id": vacancy_id},
        )

    return VacancyOut(
        id=vacancy.id,
        title=vacancy.title,
        description=vacancy.description,
        employer=vacancy.employer.name,
        department=vacancy.department.name,
        location=f"{vacancy.location.campus_zone}, {vacancy.location.room}",
        salary_per_hour=vacancy.salary_per_hour,
        workload_hours=vacancy.workload_hours,
        status=vacancy.status,
    )


@app.post("/api/vacancies/{vacancy_id}/apply", response_model=ApplicationOut, status_code=201)
def apply_to_vacancy(vacancy_id: int, payload: ApplicationCreate, db: Session = Depends(get_db)) -> ApplicationOut:
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="VACANCY_NOT_FOUND",
            user_message="Нельзя отправить отклик: вакансия не найдена.",
            developer_message=f"Apply target vacancy id={vacancy_id} not found.",
            suggestion="Обновите страницу и выберите вакансию из актуального списка.",
            details={"vacancy_id": vacancy_id},
        )

    student = db.query(Student).filter(Student.email == payload.student_email).first()
    if not student:
        student = Student(
            full_name=payload.student_full_name,
            email=payload.student_email,
            faculty=payload.faculty,
            study_year=payload.study_year,
        )
        db.add(student)
        db.flush()

    duplicate = (
        db.query(Application)
        .filter(Application.student_id == student.id, Application.vacancy_id == vacancy_id)
        .first()
    )
    if duplicate:
        raise ApiException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DUPLICATE_APPLICATION",
            user_message="Вы уже отправили отклик на эту вакансию.",
            developer_message="Unique business constraint violated: student already applied to vacancy.",
            suggestion="Проверьте статус отклика в разделе ""Мои отклики"".",
            details={"application_id": duplicate.id},
        )

    application = Application(
        student_id=student.id,
        vacancy_id=vacancy.id,
        cover_letter=payload.cover_letter,
        status="submitted",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return ApplicationOut(
        id=application.id,
        vacancy_id=vacancy.id,
        vacancy_title=vacancy.title,
        student_email=student.email,
        status=application.status,
        created_at=application.created_at,
    )


@app.get("/api/applications", response_model=list[ApplicationOut])
def list_applications(student_email: str, db: Session = Depends(get_db)) -> list[ApplicationOut]:
    student = db.query(Student).filter(Student.email == student_email).first()
    if not student:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="STUDENT_NOT_FOUND",
            user_message="Студент с таким email не найден.",
            developer_message=f"Student with email={student_email} not found.",
            suggestion="Проверьте email или сначала отправьте отклик.",
            details={"student_email": student_email},
        )

    applications = db.query(Application).filter(Application.student_id == student.id).all()

    return [
        ApplicationOut(
            id=a.id,
            vacancy_id=a.vacancy_id,
            vacancy_title=a.vacancy.title,
            student_email=student.email,
            status=a.status,
            created_at=a.created_at,
        )
        for a in applications
    ]
