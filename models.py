from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))


# =========================
# ENUM
# =========================
class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


# =========================
# 1. Quản trị viên (Web Admin)
# =========================
class AdminInfo(Base):
    __tablename__ = "admin_infos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))  # lưu password hash
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VN_TZ)
    )





# =========================
# 2. Người dùng chung: giáo viên + học sinh
# =========================

class TeleTeacherInfo(Base):
    __tablename__ = "tele_teacher_infos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)

class UserInfo(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # chủ yếu cho student
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VN_TZ)
    )

    # chỉ student mới có class_id
    class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    class_info: Mapped[Optional["ClassInfo"]] = relationship(
        "ClassInfo",
        back_populates="students",
        foreign_keys=[class_id]
    )

    homeroom_of_classes: Mapped[List["ClassInfo"]] = relationship(
        "ClassInfo",
        back_populates="homeroom_teacher",
        foreign_keys="ClassInfo.homeroom_teacher_id"
    )

    teaching_subject_classes: Mapped[List["SubjectClass"]] = relationship(
        "SubjectClass",
        back_populates="teacher_info",
        foreign_keys="SubjectClass.teacher_id"
    )

    created_assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="teacher_info",
        foreign_keys="Assignment.teacher_id"
    )

    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="student",
        foreign_keys="Submission.student_id"
    )

    points: Mapped[List["StudentPoint"]] = relationship(
        "StudentPoint",
        back_populates="student",
        foreign_keys="StudentPoint.student_id"
    )

    outgoing_join_requests: Mapped[List["RequestJoinClass"]] = relationship(
        "RequestJoinClass",
        back_populates="student",
        foreign_keys="RequestJoinClass.student_id",
    )

    announcements: Mapped[List["Announcement"]] = relationship(
        "Announcement", 
        back_populates="teacher_info",
        foreign_keys="Announcement.teacher_id",
    )
    # Không dùng CHECK trên class_id + role: MySQL 3823 — cột trong FK không kết hợp
    # được với CHECK cùng lúc. Ràng buộc nghiệp vụ (HS có lớp / GV không gán lớp như HS) xử lý ở app.


# =========================
# 3. Lớp học
# =========================
class ClassInfo(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    homeroom_teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    total_students: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    homeroom_teacher: Mapped[Optional["UserInfo"]] = relationship(
        "UserInfo",
        back_populates="homeroom_of_classes",
        foreign_keys=[homeroom_teacher_id]
    )

    students: Mapped[List["UserInfo"]] = relationship(
        "UserInfo",
        back_populates="class_info",
        foreign_keys="UserInfo.class_id"
    )

    subject_classes: Mapped[List["SubjectClass"]] = relationship(
        "SubjectClass",
        back_populates="class_info",
        cascade="all, delete-orphan"
    )

    join_requests: Mapped[List["RequestJoinClass"]] = relationship(
        "RequestJoinClass",
        back_populates="class_info",
    )

    announcements: Mapped[List["Announcement"]] = relationship(
        "Announcement", 
        back_populates="class_info",
        foreign_keys="Announcement.class_id",
    )


# =========================
# 4. Danh mục môn học
# =========================
class SubjectInfo(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    # Relationships
    subject_classes: Mapped[List["SubjectClass"]] = relationship(
        "SubjectClass",
        back_populates="subject_info",
        cascade="all, delete-orphan"
    )


# =========================
# 5. Môn học của từng lớp (môn - lớp - giáo viên)
# =========================
class SubjectClass(Base):
    __tablename__ = "subject_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        index=True
    )

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        index=True
    )

    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    subject_info: Mapped["SubjectInfo"] = relationship(
        "SubjectInfo",
        back_populates="subject_classes"
    )

    class_info: Mapped["ClassInfo"] = relationship(
        "ClassInfo",
        back_populates="subject_classes"
    )

    teacher_info: Mapped[Optional["UserInfo"]] = relationship(
        "UserInfo",
        back_populates="teaching_subject_classes",
        foreign_keys=[teacher_id]
    )

    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="subject_class",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("subject_id", "class_id", name="uix_subject_class"),
    )


# =========================
# 6. Bài tập
# =========================
class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    instruction_text: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VN_TZ)
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    subject_class_id: Mapped[int] = mapped_column(
        ForeignKey("subject_classes.id", ondelete="CASCADE"),
        index=True
    )

    # Relationships
    teacher_info: Mapped[Optional["UserInfo"]] = relationship(
        "UserInfo",
        back_populates="created_assignments",
        foreign_keys=[teacher_id]
    )

    subject_class: Mapped["SubjectClass"] = relationship(
        "SubjectClass",
        back_populates="assignments"
    )

    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )


# =========================
# 7. Bài nộp
# =========================
class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        index=True
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    file_path: Mapped[str] = mapped_column(String(500))
    ai_feedback: Mapped[str] = mapped_column(Text, default="")
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    teacher_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VN_TZ)
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(
        "Assignment",
        back_populates="submissions"
    )

    student: Mapped["UserInfo"] = relationship(
        "UserInfo",
        back_populates="submissions",
        foreign_keys=[student_id]
    )

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uix_submission_assignment_student"),
    )


# =========================
# 8. Điểm hành vi
# =========================
class StudentPoint(Base):
    __tablename__ = "student_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VN_TZ)
    )

    # Relationships
    student: Mapped["UserInfo"] = relationship(
        "UserInfo",
        back_populates="points",
        foreign_keys=[student_id]
    )



# =========================
# 9. Yêu cầu tham gia lớp học
# =========================

class RequestJoinClassStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class RequestJoinClass(Base):
    __tablename__ = "request_join_classes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        index=True
    )
    status: Mapped[RequestJoinClassStatus] = mapped_column(
        SqlEnum(RequestJoinClassStatus, name="request_join_class_status"),
        default=RequestJoinClassStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(VN_TZ))

    student: Mapped["UserInfo"] = relationship(
        "UserInfo",
        back_populates="outgoing_join_requests",
        foreign_keys=[student_id],
    )
    class_info: Mapped["ClassInfo"] = relationship(
        "ClassInfo",
        back_populates="join_requests",
        foreign_keys=[class_id],
    )



class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    message: Mapped[str] = mapped_column(Text)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(VN_TZ))

    teacher_info: Mapped["UserInfo"] = relationship(
        "UserInfo",
        back_populates="announcements",
        foreign_keys=[teacher_id],
    )

    class_info: Mapped["ClassInfo"] = relationship(
        "ClassInfo",
        back_populates="announcements",
        foreign_keys=[class_id],
    )