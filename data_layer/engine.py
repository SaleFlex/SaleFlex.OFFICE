"""
Database engine singleton for SaleFlex.OFFICE data layer.
"""

from contextlib import contextmanager
from pathlib import Path
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from settings.settings import Settings


class Engine:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if Engine._initialized:
            return

        settings = Settings()
        project_root = Path(__file__).resolve().parents[1]
        db_file_name = settings.database_name.strip() or "office.sqlite3"
        db_path = project_root / db_file_name
        legacy_db_path = project_root / "database" / db_file_name
        legacy_default_db_path = project_root / "database" / "office.sqlite3"

        if legacy_db_path.exists() and not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_db_path), str(db_path))
        elif legacy_default_db_path.exists() and not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_default_db_path), str(db_path))
        self.db_path = db_path

        self.engine = create_engine(
            f"sqlite:///{db_path}",
            pool_pre_ping=True,
            echo=False,
        )
        self.SessionFactory = sessionmaker(bind=self.engine, expire_on_commit=False)
        Engine._initialized = True

    @contextmanager
    def get_session(self):
        """Context manager for safe session management."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def session(self):
        """Legacy access helper for direct session use."""
        if not hasattr(self, "_session") or self._session is None:
            self._session = self.SessionFactory()
        return self._session

    def close_session(self):
        """Close active legacy session if available."""
        if hasattr(self, "_session") and self._session:
            self._session.close()
            self._session = None

