from typing import Optional

from pydantic import BaseModel, Field


class TeleTeacherCreate(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=255)
    username: Optional[str] = Field(default=None, max_length=255)


class TeleTeacherOut(BaseModel):
    id: int
    telegram_id: str
    username: Optional[str] = None

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class SubjectOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    homeroom_teacher_id: Optional[int] = None


class HomeroomUpdate(BaseModel):
    homeroom_teacher_id: Optional[int] = None


class ClassOut(BaseModel):
    id: int
    name: str
    total_students: int
    homeroom_teacher_id: Optional[int] = None
    homeroom_teacher_name: Optional[str] = Field(
        default=None,
        description="Họ tên giáo viên chủ nhiệm (bảng users.full_name) khi đã gán GVCN",
    )


class StudentOut(BaseModel):
    id: int
    telegram_id: str
    username: Optional[str]
    full_name: str
    is_active: bool
    is_blocked: bool
    class_id: Optional[int]

    class Config:
        from_attributes = True


class SubjectClassCreate(BaseModel):
    subject_id: int
    class_id: int
    teacher_id: Optional[int] = None


class SubjectClassTeacherUpdate(BaseModel):
    teacher_id: Optional[int] = None


class SubjectClassOut(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    class_id: int
    class_name: str
    teacher_id: Optional[int]
    teacher_name: Optional[str]


class TeacherOut(BaseModel):
    """Giáo viên = UserInfo có role = teacher (bảng `users`)."""

    id: int
    telegram_id: str
    username: Optional[str] = None
    full_name: str
    is_active: bool
    homeroom_classes: list[ClassOut]

    class Config:
        from_attributes = True
