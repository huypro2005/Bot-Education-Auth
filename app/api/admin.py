from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.service import admin as admin_crud
from app.schemas.admin import (
    ClassCreate,
    ClassOut,
    HomeroomUpdate,
    StudentOut,
    SubjectClassCreate,
    SubjectClassOut,
    SubjectClassTeacherUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
    TeleTeacherCreate,
    TeleTeacherOut,
    TeacherOut,
)
from database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def _map_class_out(class_info) -> ClassOut:
    return ClassOut(
        id=class_info.id,
        name=class_info.name,
        total_students=class_info.total_students,
        homeroom_teacher_id=class_info.homeroom_teacher_id,
        homeroom_teacher_name=class_info.homeroom_teacher.full_name if class_info.homeroom_teacher else None,
    )


def _map_subject_class_out(record) -> SubjectClassOut:
    return SubjectClassOut(
        id=record.id,
        subject_id=record.subject_id,
        subject_name=record.subject_info.name,
        class_id=record.class_id,
        class_name=record.class_info.name,
        teacher_id=record.teacher_id,
        teacher_name=record.teacher_info.full_name if record.teacher_info else None,
    )


def _map_teacher_out(user) -> TeacherOut:
    return TeacherOut(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        homeroom_classes=[_map_class_out(c) for c in user.homeroom_of_classes],
    )


# --- TeleTeacher whitelist ---
@router.post("/tele-teachers", response_model=TeleTeacherOut, status_code=status.HTTP_201_CREATED)
def create_tele_teacher(payload: TeleTeacherCreate, db: Session = Depends(get_db)):
    return admin_crud.create_tele_teacher(db=db, telegram_id=payload.telegram_id, username=payload.username)


@router.get("/tele-teachers", response_model=list[TeleTeacherOut])
def list_tele_teachers(db: Session = Depends(get_db)):
    return admin_crud.list_tele_teachers(db)


@router.delete("/tele-teachers/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tele_teacher(record_id: int, db: Session = Depends(get_db)):
    admin_crud.delete_tele_teacher(db, record_id)


# --- Teachers (users.role = teacher) ---
@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(db: Session = Depends(get_db)):
    return [_map_teacher_out(item) for item in admin_crud.list_teachers(db)]


# --- Subjects ---
@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)):
    return admin_crud.create_subject(db=db, name=payload.name, description=payload.description)


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return admin_crud.list_subjects(db)


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db)):
    return admin_crud.update_subject(
        db=db,
        record_id=subject_id,
        name=payload.name,
        description=payload.description,
    )


# --- Classes ---
@router.post("/classes", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):
    class_info = admin_crud.create_class(
        db=db,
        name=payload.name,
        homeroom_teacher_id=payload.homeroom_teacher_id,
    )
    return _map_class_out(class_info)


@router.get("/classes", response_model=list[ClassOut])
def list_classes(db: Session = Depends(get_db)):
    return [_map_class_out(item) for item in admin_crud.list_classes(db)]


@router.put("/classes/{class_id}/homeroom", response_model=ClassOut)
def update_homeroom_teacher(class_id: int, payload: HomeroomUpdate, db: Session = Depends(get_db)):
    class_info = admin_crud.update_homeroom_teacher(
        db=db, class_id=class_id, homeroom_teacher_id=payload.homeroom_teacher_id
    )
    return _map_class_out(class_info)


@router.get("/classes/{class_id}/students", response_model=list[StudentOut])
def list_students_of_class(class_id: int, db: Session = Depends(get_db)):
    return admin_crud.list_students_of_class(db=db, class_id=class_id)


# --- SubjectClass (môn theo lớp + GV) ---
@router.post("/subject-classes", response_model=SubjectClassOut, status_code=status.HTTP_201_CREATED)
def create_subject_class(payload: SubjectClassCreate, db: Session = Depends(get_db)):
    record = admin_crud.create_subject_class(
        db=db,
        subject_id=payload.subject_id,
        class_id=payload.class_id,
        teacher_id=payload.teacher_id,
    )
    return _map_subject_class_out(record)


@router.get("/subject-classes", response_model=list[SubjectClassOut])
def list_subject_classes(
    class_id: Optional[int] = Query(default=None, description="Lọc theo lớp; bỏ trống = tất cả"),
    db: Session = Depends(get_db),
):
    return [_map_subject_class_out(item) for item in admin_crud.list_subject_classes(db=db, class_id=class_id)]


@router.get("/classes/{class_id}/subject-classes", response_model=list[SubjectClassOut])
def list_subject_classes_for_class(class_id: int, db: Session = Depends(get_db)):
    """Tất cả môn-học (SubjectClass) thuộc một lớp."""
    if not admin_crud.get_class_or_none(db, class_id):
        raise HTTPException(status_code=404, detail="class not found")
    return [_map_subject_class_out(item) for item in admin_crud.list_subject_classes(db=db, class_id=class_id)]


@router.put("/subject-classes/{subject_class_id}/teacher", response_model=SubjectClassOut)
def update_subject_class_teacher(
    subject_class_id: int, payload: SubjectClassTeacherUpdate, db: Session = Depends(get_db)
):
    record = admin_crud.update_subject_class_teacher(
        db=db, record_id=subject_class_id, teacher_id=payload.teacher_id
    )
    return _map_subject_class_out(record)
