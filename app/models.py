from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# 1. Quản trị viên (Web Admin)
class AdminInfo(Base):
    __tablename__ = "admin_infos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255)) # Nên lưu hash
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

# 2. Danh sách giáo viên được phép dùng Bot
class TeleTeacherInfo(Base):
    __tablename__ = "tele_teacher_infos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)

# 3. Thông tin chi tiết Giáo viên
class TeacherInfo(Base):
    __tablename__ = "teachers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    homeroom_classes: Mapped[List["ClassInfo"]] = relationship("ClassInfo", back_populates="homeroom_teacher")
    subject_classes: Mapped[List["SubjectClass"]] = relationship("SubjectClass", back_populates="teacher_info")
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="teacher_info")

# 4. Thông tin Lớp học
class ClassInfo(Base):
    __tablename__ = "classes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    homeroom_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"), index=True)
    total_students: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    homeroom_teacher: Mapped[Optional["TeacherInfo"]] = relationship("TeacherInfo", back_populates="homeroom_classes")
    students: Mapped[List["StudentInfo"]] = relationship("StudentInfo", back_populates="class_info")
    subject_classes: Mapped[List["SubjectClass"]] = relationship("SubjectClass", back_populates="class_info")

# 5. Thông tin Học sinh (1 học sinh - 1 lớp)
class StudentInfo(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"), index=True)
    
    # Relationships
    class_info: Mapped[Optional["ClassInfo"]] = relationship("ClassInfo", back_populates="students")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="student")
    points: Mapped[List["StudentPoint"]] = relationship("StudentPoint", back_populates="student")

# 6. Danh mục Môn học
class SubjectInfo(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")

    # Relationships
    subject_classes: Mapped[List["SubjectClass"]] = relationship("SubjectClass", back_populates="subject_info")

# 7. Môn học cụ thể của từng Lớp (Nối Môn - Lớp - Giáo viên)
class SubjectClass(Base):
    __tablename__ = "subject_classes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"), index=True)

    # Relationships
    subject_info: Mapped["SubjectInfo"] = relationship("SubjectInfo", back_populates="subject_classes")
    class_info: Mapped["ClassInfo"] = relationship("ClassInfo", back_populates="subject_classes")
    teacher_info: Mapped[Optional["TeacherInfo"]] = relationship("TeacherInfo", back_populates="subject_classes")
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="subject_class")

    __table_args__ = (
        UniqueConstraint("subject_id", "class_id", name="uix_subject_class_subject_class"),
    )

# 8. Bài tập
class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    instruction_text: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"), index=True)
    subject_class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subject_classes.id"), index=True)

    # Relationships
    teacher_info: Mapped[Optional["TeacherInfo"]] = relationship("TeacherInfo", back_populates="assignments")
    subject_class: Mapped[Optional["SubjectClass"]] = relationship("SubjectClass", back_populates="assignments")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="assignment")

# 9. Bài nộp
class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(500))
    ai_feedback: Mapped[str] = mapped_column(Text, default="")
    ai_score: Mapped[Optional[float]] = mapped_column(Float)
    teacher_score: Mapped[Optional[float]] = mapped_column(Float)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["StudentInfo"] = relationship("StudentInfo", back_populates="submissions")

    # unique constraint for assignment_id and student_id
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uix_submission_assignment_student"),)

# 10. Điểm hành vi
class StudentPoint(Base):
    __tablename__ = "student_points"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    student: Mapped["StudentInfo"] = relationship("StudentInfo", back_populates="points")

class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message: Mapped[str] = mapped_column(Text)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    