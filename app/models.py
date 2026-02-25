from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    faculty: Mapped[str] = mapped_column(String(120), nullable=False)
    study_year: Mapped[int] = mapped_column(Integer, nullable=False)

    applications = relationship("Application", back_populates="student")


class Employer(Base):
    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    employer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(120), nullable=False)

    vacancies = relationship("Vacancy", back_populates="employer")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    building: Mapped[str] = mapped_column(String(80), nullable=False)

    vacancies = relationship("Vacancy", back_populates="department")


class VacancyCategory(Base):
    __tablename__ = "vacancy_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)

    vacancies = relationship("Vacancy", back_populates="category")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campus_zone: Mapped[str] = mapped_column(String(80), nullable=False)
    room: Mapped[str] = mapped_column(String(20), nullable=False)

    vacancies = relationship("Vacancy", back_populates="location")


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")
    salary_per_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    workload_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employer_id: Mapped[int] = mapped_column(ForeignKey("employers.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("vacancy_categories.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    employer = relationship("Employer", back_populates="vacancies")
    department = relationship("Department", back_populates="vacancies")
    category = relationship("VacancyCategory", back_populates="vacancies")
    location = relationship("Location", back_populates="vacancies")
    applications = relationship("Application", back_populates="vacancy")
    skills = relationship("VacancySkill", back_populates="vacancy")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    vacancies = relationship("VacancySkill", back_populates="skill")


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)

    vacancy = relationship("Vacancy", back_populates="skills")
    skill = relationship("Skill", back_populates="vacancies")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False)

    student = relationship("Student", back_populates="applications")
    vacancy = relationship("Vacancy", back_populates="applications")
    status_history = relationship("ApplicationStatusHistory", back_populates="application")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    old_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="status_history")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
