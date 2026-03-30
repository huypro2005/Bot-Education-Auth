import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Add it to your .env file.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def _ensure_request_join_classes_student_id_mysql() -> None:
    """create_all() không ALTER bảng cũ; bổ sung cột student_id nếu thiếu."""
    if engine.dialect.name != "mysql":
        return
    insp = inspect(engine)
    if "request_join_classes" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("request_join_classes")}
    if "student_id" in cols:
        return
    with engine.begin() as conn:
        if "user_id" in cols:
            conn.execute(
                text(
                    "ALTER TABLE request_join_classes "
                    "CHANGE COLUMN user_id student_id INT NOT NULL"
                )
            )
            return
        conn.execute(
            text(
                "ALTER TABLE request_join_classes "
                "ADD COLUMN student_id INT NULL AFTER id"
            )
        )
        n = conn.execute(text("SELECT COUNT(*) FROM request_join_classes")).scalar()
        if n:
            conn.execute(
                text("DELETE FROM request_join_classes WHERE student_id IS NULL")
            )
        conn.execute(
            text(
                "ALTER TABLE request_join_classes "
                "MODIFY COLUMN student_id INT NOT NULL"
            )
        )
        fk = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'request_join_classes'
                  AND COLUMN_NAME = 'student_id'
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                """
            )
        ).scalar()
        if not fk:
            conn.execute(
                text(
                    "ALTER TABLE request_join_classes "
                    "ADD CONSTRAINT fk_request_join_classes_student "
                    "FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE"
                )
            )

def _ensure_announcements_class_id_mysql() -> None:
    if engine.dialect.name != "mysql":
        return
    insp = inspect(engine)
    if "announcements" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("announcements")}
    if "class_id" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE announcements "
                "ADD COLUMN class_id INT NOT NULL AFTER id"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE announcements "
                "ADD CONSTRAINT fk_announcements_class "
                "FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE"
            )
        )

def _ensure_announcements_teacher_id_mysql() -> None:
    if engine.dialect.name != "mysql":
        return
    insp = inspect(engine)
    if "announcements" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("announcements")}
    if "teacher_id" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE announcements "
                "ADD COLUMN teacher_id INT NOT NULL AFTER id"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE announcements "
                "ADD CONSTRAINT fk_announcements_teacher "
                "FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE"
            )
        )
    
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_request_join_classes_student_id_mysql()
    _ensure_announcements_class_id_mysql()
    _ensure_announcements_teacher_id_mysql()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()