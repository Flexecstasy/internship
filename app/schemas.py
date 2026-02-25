from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ApiError(BaseModel):
    error_code: str
    user_message: str
    developer_message: str
    suggestion: str
    details: dict | None = None


class VacancyOut(BaseModel):
    id: int
    title: str
    description: str
    employer: str
    department: str
    location: str
    salary_per_hour: int
    workload_hours: int
    status: str


class ApplicationCreate(BaseModel):
    student_email: EmailStr
    student_full_name: str = Field(min_length=3, max_length=120)
    faculty: str = Field(min_length=2, max_length=120)
    study_year: int = Field(ge=1, le=6)
    cover_letter: str = Field(min_length=30, max_length=2000)


class ApplicationOut(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: str
    student_email: EmailStr
    status: str
    created_at: datetime


class HealthOut(BaseModel):
    status: str
