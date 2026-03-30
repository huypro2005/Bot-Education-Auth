from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from models import ClassInfo, SubjectClass, SubjectInfo, TeleTeacherInfo, UserInfo, UserRole


def _teacher_or_404(db: Session, user_id: int) -> UserInfo:
    u = db.get(UserInfo, user_id)
    if u is None or u.role != UserRole.TEACHER:
        raise HTTPException(status_code=404, detail="teacher not found")
    return u


def create_tele_teacher(db: Session, telegram_id: str, username: Optional[str]):
    record = TeleTeacherInfo(telegram_id=telegram_id, username=username)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="telegram_id already exists in whitelist")
    db.refresh(record)
    return record


def list_tele_teachers(db: Session):
    return db.query(TeleTeacherInfo).order_by(TeleTeacherInfo.id.desc()).all()


def delete_tele_teacher(db: Session, record_id: int):
    record = db.get(TeleTeacherInfo, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="tele_teacher not found")
    db.delete(record)
    db.commit()


def create_subject(db: Session, name: str, description: str):
    record = SubjectInfo(name=name.strip(), description=description.strip())
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="subject name already exists")
    db.refresh(record)
    return record


def list_subjects(db: Session):
    return db.query(SubjectInfo).order_by(SubjectInfo.id.desc()).all()


def update_subject(db: Session, record_id: int, name: Optional[str], description: Optional[str]):
    record = db.get(SubjectInfo, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="subject not found")
    if name is not None:
        record.name = name.strip()
    if description is not None:
        record.description = description.strip()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="subject name already exists")
    db.refresh(record)
    return record


def create_class(db: Session, name: str, homeroom_teacher_id: Optional[int]):
    if homeroom_teacher_id is not None:
        _teacher_or_404(db, homeroom_teacher_id)

    record = ClassInfo(name=name.strip(), homeroom_teacher_id=homeroom_teacher_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="class name already exists")
    loaded = _load_class_with_homeroom_teacher(db, record.id)
    if loaded is None:
        raise HTTPException(status_code=500, detail="failed to load class after create")
    return loaded


def get_class_or_none(db: Session, class_id: int) -> Optional[ClassInfo]:
    return db.get(ClassInfo, class_id)


def _load_class_with_homeroom_teacher(db: Session, class_id: int) -> Optional[ClassInfo]:
    """Luôn joinedload UserInfo GVCN để API trả về homeroom_teacher_name ổn định."""
    return (
        db.query(ClassInfo)
        .options(joinedload(ClassInfo.homeroom_teacher))
        .filter(ClassInfo.id == class_id)
        .one_or_none()
    )


def list_classes(db: Session):
    return (
        db.query(ClassInfo)
        .options(joinedload(ClassInfo.homeroom_teacher))
        .order_by(ClassInfo.id.desc())
        .all()
    )


def update_homeroom_teacher(db: Session, class_id: int, homeroom_teacher_id: Optional[int]):
    class_info = db.get(ClassInfo, class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="class not found")

    if homeroom_teacher_id is not None:
        _teacher_or_404(db, homeroom_teacher_id)

    class_info.homeroom_teacher_id = homeroom_teacher_id
    db.commit()
    loaded = _load_class_with_homeroom_teacher(db, class_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail="class not found")
    return loaded


def list_students_of_class(db: Session, class_id: int):
    class_info = db.get(ClassInfo, class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="class not found")
    return (
        db.query(UserInfo)
        .filter(UserInfo.class_id == class_id)
        .filter(UserInfo.role == UserRole.STUDENT)
        .order_by(UserInfo.id.asc())
        .all()
    )


def create_subject_class(db: Session, subject_id: int, class_id: int, teacher_id: Optional[int]):
    subject = db.get(SubjectInfo, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="subject not found")

    class_info = db.get(ClassInfo, class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="class not found")

    if teacher_id is not None:
        _teacher_or_404(db, teacher_id)

    record = SubjectClass(subject_id=subject_id, class_id=class_id, teacher_id=teacher_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="subject already assigned to this class")
    db.refresh(record)
    return record


def update_subject_class_teacher(db: Session, record_id: int, teacher_id: Optional[int]):
    record = db.get(SubjectClass, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="subject_class not found")

    if teacher_id is not None:
        _teacher_or_404(db, teacher_id)

    record.teacher_id = teacher_id
    db.commit()
    db.refresh(record)
    return record


def list_subject_classes(db: Session, class_id: Optional[int]):
    query = db.query(SubjectClass).options(
        joinedload(SubjectClass.subject_info),
        joinedload(SubjectClass.class_info),
        joinedload(SubjectClass.teacher_info),
    )
    if class_id is not None:
        query = query.filter(SubjectClass.class_id == class_id)
    return query.order_by(SubjectClass.id.desc()).all()


def list_teachers(db: Session):
    return (
        db.query(UserInfo)
        .filter(UserInfo.role == UserRole.TEACHER)
        .options(
            joinedload(UserInfo.homeroom_of_classes).joinedload(ClassInfo.homeroom_teacher),
        )
        .order_by(UserInfo.id.desc())
        .all()
    )
