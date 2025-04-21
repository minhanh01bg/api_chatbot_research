# src/exceptions.py
from fastapi import HTTPException, status

class AppBaseException(HTTPException):
    """Lớp cơ sở cho tất cả ngoại lệ trong ứng dụng."""
    def __init__(self, status_code: int, detail: str, error_code: str = "GENERIC_ERROR"):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail)

class DatabaseConnectionError(AppBaseException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to the database",
            error_code="DB_CONNECTION_FAILED"
        )