"""
Authentication service for SaleFlex.OFFICE login flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from core.logger import get_logger
from data_layer.engine import Engine
from data_layer.model.definition.cashier import Cashier


logger = get_logger(__name__)


@dataclass(frozen=True)
class AuthResult:
    """Authentication response payload for login UI."""

    success: bool
    message: str
    username: str = ""


class AuthService:
    """Authenticate users against the cashier table."""

    def __init__(self) -> None:
        self.engine = Engine()

    def authenticate(self, username: str, password: str) -> AuthResult:
        """Validate username/password with an active cashier record."""
        normalized_username = username.strip()
        if not normalized_username or not password:
            return AuthResult(success=False, message="Please enter both username and password.")

        try:
            with self.engine.get_session() as session:
                cashier = (
                    session.query(Cashier)
                    .filter(
                        Cashier.user_name == normalized_username,
                        Cashier.is_deleted.is_(False),
                    )
                    .first()
                )

                if cashier is None:
                    return AuthResult(success=False, message="Invalid username or password.")

                if not cashier.is_active:
                    return AuthResult(success=False, message="This user is inactive. Contact administrator.")

                if not cashier.is_administrator and not cashier.is_manager:
                    return AuthResult(
                        success=False,
                        message="This user does not have Office access permission.",
                    )

                if cashier.password != password:
                    return AuthResult(success=False, message="Invalid username or password.")

                cashier.login_at = datetime.now(timezone.utc).replace(tzinfo=None)
                return AuthResult(
                    success=True,
                    message=f"Login successful. Welcome {cashier.user_name}.",
                    username=cashier.user_name,
                )
        except SQLAlchemyError:
            logger.exception("Database authentication failed for user '%s'.", normalized_username)
            return AuthResult(
                success=False,
                message="Authentication failed due to a database error.",
            )
