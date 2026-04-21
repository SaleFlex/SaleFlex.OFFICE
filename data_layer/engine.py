"""
Database engine singleton for SaleFlex.OFFICE data layer.
"""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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

        project_root = Path(__file__).resolve().parents[1]
        db_dir = project_root / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "office.sqlite3"

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

