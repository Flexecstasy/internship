from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


class ApiException(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        user_message: str,
        developer_message: str,
        suggestion: str,
        details: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.user_message = user_message
        self.developer_message = developer_message
        self.suggestion = suggestion
        self.details = details or {}


def error_payload(exc: ApiException) -> dict:
    return {
        "error_code": exc.error_code,
        "user_message": exc.user_message,
        "developer_message": exc.developer_message,
        "suggestion": exc.suggestion,
        "details": exc.details,
    }


async def api_exception_handler(_: Request, exc: ApiException):
    return JSONResponse(status_code=exc.status_code, content=error_payload(exc))


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    fields = []
    for err in exc.errors():
        loc = ".".join([str(v) for v in err.get("loc", []) if v != "body"])
        fields.append({"field": loc, "issue": err.get("msg", "invalid value")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "user_message": "Некоторые поля заполнены неверно.",
            "developer_message": "Request body/query/path validation failed.",
            "suggestion": "Проверьте формат и обязательность полей в документации Swagger.",
            "details": {"fields": fields},
        },
    )


async def generic_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "user_message": "На сервере произошла ошибка.",
            "developer_message": str(exc),
            "suggestion": "Повторите попытку позже или обратитесь к разработчику.",
            "details": {},
        },
    )
