from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    def __init__(self, user_id: int):
        detail = f"User with ID {user_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidCredentialsError(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Invalid email or password")
