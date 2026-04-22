"""
Service layer for cashier management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.cashier_performance_target import CashierPerformanceTarget
from data_layer.model.definition.cashier_transaction_metrics import CashierTransactionMetrics
from data_layer.model.definition.store import Store


@dataclass(frozen=True)
class ServiceResult:
    """Simple operation result used by UI forms."""

    success: bool
    message: str


@dataclass(frozen=True)
class CashierView:
    """Read model for cashier grid."""

    id: str
    no: int
    user_name: str
    name: str
    last_name: str
    password: str
    identity_number: str
    description: str
    is_administrator: bool
    is_manager: bool
    is_active: bool
    login_at: datetime | None


@dataclass(frozen=True)
class CashierPerformanceTargetView:
    """Read model for performance target grid."""

    id: str
    cashier_id: str
    cashier_name: str
    target_period: str
    target_start_date: date
    target_end_date: date
    target_total_sales: Decimal | None
    target_transactions_count: int | None
    current_achievement_percentage: float
    target_status: str
    is_on_track: bool
    target_description: str


@dataclass(frozen=True)
class CashierTransactionMetricView:
    """Read model for cashier transaction metric grid."""

    id: str
    cashier_id: str
    cashier_name: str
    transaction_start_time: datetime
    transaction_end_time: datetime | None
    total_transaction_time: float | None
    transaction_total_amount: Decimal
    number_of_items: int
    payment_method_used: str | None
    transaction_efficiency_score: float | None
    transaction_complexity_level: str
    transaction_cancelled: bool
    transaction_notes: str | None


class CashierManagementService:
    """Coordinate cashier CRUD, target setup, and transaction metrics views."""

    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_cashiers(self) -> list[CashierView]:
        """Return active cashier records for grid rendering."""
        with self._engine.get_session() as session:
            rows = (
                session.query(Cashier)
                .filter(Cashier.is_deleted.is_(False))
                .order_by(asc(Cashier.no))
                .all()
            )
            return [
                CashierView(
                    id=str(row.id),
                    no=row.no,
                    user_name=row.user_name,
                    name=row.name,
                    last_name=row.last_name,
                    password=row.password,
                    identity_number=row.identity_number,
                    description=row.description or "",
                    is_administrator=bool(row.is_administrator),
                    is_manager=bool(row.is_manager),
                    is_active=bool(row.is_active),
                    login_at=row.login_at,
                )
                for row in rows
            ]

    def save_cashier(self, payload: dict[str, Any], cashier_id: str | None = None) -> ServiceResult:
        """Create or update cashier record after validations."""
        username = str(payload.get("user_name", "")).strip()
        name = str(payload.get("name", "")).strip()
        last_name = str(payload.get("last_name", "")).strip()
        password = str(payload.get("password", "")).strip()
        identity_number = str(payload.get("identity_number", "")).strip()
        description = str(payload.get("description", "")).strip()

        if not username or not name or not last_name:
            return ServiceResult(
                success=False,
                message="Username, name, and last name are required.",
            )

        if cashier_id is None and not password:
            return ServiceResult(
                success=False,
                message="Password is required for a new cashier.",
            )

        try:
            with self._engine.get_session() as session:
                existing_by_username = (
                    session.query(Cashier)
                    .filter(
                        Cashier.user_name == username,
                        Cashier.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_username and str(existing_by_username.id) != str(cashier_id):
                    return ServiceResult(
                        success=False,
                        message=f"Username '{username}' is already in use.",
                    )

                no_value = int(payload.get("no", 0))
                existing_by_no = (
                    session.query(Cashier)
                    .filter(
                        Cashier.no == no_value,
                        Cashier.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_no and str(existing_by_no.id) != str(cashier_id):
                    return ServiceResult(
                        success=False,
                        message=f"Cashier number '{no_value}' is already in use.",
                    )

                if cashier_id:
                    cashier = (
                        session.query(Cashier)
                        .filter(
                            Cashier.id == self._as_uuid(cashier_id),
                            Cashier.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if cashier is None:
                        return ServiceResult(success=False, message="Cashier record not found.")
                else:
                    cashier = Cashier()

                cashier.no = no_value
                cashier.user_name = username
                cashier.name = name
                cashier.last_name = last_name
                if password:
                    cashier.password = password
                cashier.identity_number = identity_number
                cashier.description = description
                cashier.is_administrator = bool(payload.get("is_administrator", False))
                cashier.is_manager = bool(payload.get("is_manager", False))
                cashier.is_active = bool(payload.get("is_active", False))

                if not cashier_id:
                    session.add(cashier)

                return ServiceResult(
                    success=True,
                    message="Cashier updated successfully."
                    if cashier_id
                    else "Cashier created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Cashier save operation failed due to a database error.",
            )

    def delete_cashier(self, cashier_id: str) -> ServiceResult:
        """Soft delete cashier by marking it as deleted."""
        try:
            with self._engine.get_session() as session:
                cashier = (
                    session.query(Cashier)
                    .filter(
                        Cashier.id == self._as_uuid(cashier_id),
                        Cashier.is_deleted.is_(False),
                    )
                    .first()
                )
                if cashier is None:
                    return ServiceResult(success=False, message="Cashier record not found.")
                cashier.is_deleted = True
                return ServiceResult(success=True, message="Cashier deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Cashier delete operation failed due to a database error.",
            )

    def list_performance_targets(
        self,
        cashier_id: str | None = None,
    ) -> list[CashierPerformanceTargetView]:
        """Return configured performance targets with optional cashier filtering."""
        try:
            with self._engine.get_session() as session:
                query = (
                    session.query(CashierPerformanceTarget, Cashier)
                    .join(Cashier, Cashier.id == CashierPerformanceTarget.fk_cashier_id)
                    .filter(
                        CashierPerformanceTarget.is_deleted.is_(False),
                        Cashier.is_deleted.is_(False),
                    )
                    .order_by(
                        asc(Cashier.no),
                        asc(CashierPerformanceTarget.target_start_date),
                    )
                )
                if cashier_id:
                    query = query.filter(
                        CashierPerformanceTarget.fk_cashier_id == self._as_uuid(cashier_id)
                    )

                rows = query.all()
                return [
                    CashierPerformanceTargetView(
                        id=str(target.id),
                        cashier_id=str(cashier.id),
                        cashier_name=f"{cashier.name} {cashier.last_name}".strip(),
                        target_period=target.target_period,
                        target_start_date=target.target_start_date,
                        target_end_date=target.target_end_date,
                        target_total_sales=target.target_total_sales,
                        target_transactions_count=target.target_transactions_count,
                        current_achievement_percentage=float(
                            target.current_achievement_percentage or 0.0
                        ),
                        target_status=target.target_status,
                        is_on_track=bool(target.is_on_track),
                        target_description=target.target_description or "",
                    )
                    for target, cashier in rows
                ]
        except (SQLAlchemyError, ValueError):
            return []

    def save_performance_target(
        self,
        payload: dict[str, Any],
        target_id: str | None = None,
    ) -> ServiceResult:
        """Create or update cashier performance target definition."""
        cashier_id = str(payload.get("cashier_id", "")).strip()
        if not cashier_id:
            return ServiceResult(success=False, message="Cashier selection is required.")

        start_date = payload.get("target_start_date")
        end_date = payload.get("target_end_date")
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            return ServiceResult(success=False, message="Target start and end dates are required.")

        store_id = self._resolve_store_id()
        if store_id is None:
            return ServiceResult(
                success=False,
                message="Active store definition was not found for performance targets.",
            )

        try:
            with self._engine.get_session() as session:
                if target_id:
                    target = (
                        session.query(CashierPerformanceTarget)
                        .filter(
                            CashierPerformanceTarget.id == self._as_uuid(target_id),
                            CashierPerformanceTarget.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if target is None:
                        return ServiceResult(
                            success=False,
                            message="Performance target record not found.",
                        )
                else:
                    target = CashierPerformanceTarget()
                    session.add(target)

                target.fk_cashier_id = self._as_uuid(cashier_id)
                target.fk_store_id = self._as_uuid(store_id)
                target.target_type = "INDIVIDUAL"
                target.target_period = str(payload.get("target_period", "MONTHLY"))
                target.target_start_date = start_date
                target.target_end_date = end_date
                target.target_year = start_date.year
                target.target_month = start_date.month if target.target_period == "MONTHLY" else None
                target.target_week = int(start_date.strftime("%V")) if target.target_period == "WEEKLY" else None
                target.target_total_sales = Decimal(str(payload.get("target_total_sales", "0")))
                target.target_transactions_count = int(payload.get("target_transactions_count", 0))
                target.current_achievement_percentage = float(
                    payload.get("current_achievement_percentage", 0.0)
                )
                target.target_status = str(payload.get("target_status", "ACTIVE"))
                target.is_on_track = bool(payload.get("is_on_track", True))
                target.target_description = str(payload.get("target_description", "")).strip()

                return ServiceResult(
                    success=True,
                    message="Performance target updated successfully."
                    if target_id
                    else "Performance target created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(
                success=False,
                message="Performance target save operation failed due to a database error.",
            )

    def delete_performance_target(self, target_id: str) -> ServiceResult:
        """Soft delete performance target by id."""
        try:
            with self._engine.get_session() as session:
                target = (
                    session.query(CashierPerformanceTarget)
                    .filter(
                        CashierPerformanceTarget.id == self._as_uuid(target_id),
                        CashierPerformanceTarget.is_deleted.is_(False),
                    )
                    .first()
                )
                if target is None:
                    return ServiceResult(success=False, message="Performance target not found.")
                target.is_deleted = True
                return ServiceResult(
                    success=True,
                    message="Performance target deleted successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Performance target delete operation failed due to a database error.",
            )

    def list_transaction_metrics(
        self,
        cashier_id: str | None = None,
        limit: int = 500,
    ) -> list[CashierTransactionMetricView]:
        """Return cashier transaction metrics ordered by transaction start date."""
        try:
            with self._engine.get_session() as session:
                query = (
                    session.query(CashierTransactionMetrics, Cashier)
                    .join(Cashier, Cashier.id == CashierTransactionMetrics.fk_cashier_id)
                    .filter(
                        CashierTransactionMetrics.is_deleted.is_(False),
                        Cashier.is_deleted.is_(False),
                    )
                    .order_by(CashierTransactionMetrics.transaction_start_time.desc())
                )
                if cashier_id:
                    query = query.filter(
                        CashierTransactionMetrics.fk_cashier_id == self._as_uuid(cashier_id)
                    )

                rows = query.limit(limit).all()
                return [
                    CashierTransactionMetricView(
                        id=str(metric.id),
                        cashier_id=str(cashier.id),
                        cashier_name=f"{cashier.name} {cashier.last_name}".strip(),
                        transaction_start_time=metric.transaction_start_time,
                        transaction_end_time=metric.transaction_end_time,
                        total_transaction_time=metric.total_transaction_time,
                        transaction_total_amount=metric.transaction_total_amount or Decimal("0"),
                        number_of_items=int(metric.number_of_items or 0),
                        payment_method_used=metric.payment_method_used,
                        transaction_efficiency_score=metric.transaction_efficiency_score,
                        transaction_complexity_level=metric.transaction_complexity_level,
                        transaction_cancelled=bool(metric.transaction_cancelled),
                        transaction_notes=metric.transaction_notes,
                    )
                    for metric, cashier in rows
                ]
        except (SQLAlchemyError, ValueError):
            return []

    def _resolve_store_id(self) -> str | None:
        """Resolve store id based on configured store code with fallback to first active store."""
        with self._engine.get_session() as session:
            store = (
                session.query(Store)
                .filter(
                    Store.store_code == self._store_code,
                    Store.is_deleted.is_(False),
                )
                .first()
            )
            if store is None:
                store = (
                    session.query(Store)
                    .filter(Store.is_deleted.is_(False))
                    .order_by(asc(Store.store_code))
                    .first()
                )
            return str(store.id) if store is not None else None

    @staticmethod
    def _as_uuid(value: str | None) -> UUID | None:
        """Convert external string ids to UUID for SQLAlchemy comparisons."""
        if value is None:
            return None
        return UUID(str(value))
