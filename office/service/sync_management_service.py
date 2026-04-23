"""
Service layer for the Data Sync and Backup management module.

Covers: SyncQueueItem outbox management and GateNotification inbox listing.

The SyncQueueItem table is the offline outbox for all external integrations.
This service provides read/list/action methods so the SyncManagementForm can
display queue state and let operators intervene (retry failed items, delete stale
records, clear sent history).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.gate_notification import GateNotification
from data_layer.model.definition.sync_queue_item import SyncQueueItem


# ---------------------------------------------------------------------------
# Shared result wrapper
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServiceResult:
    """Simple operation result used by UI forms."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# View dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SyncQueueItemView:
    """Read-only projection of a SyncQueueItem row for the grid."""

    id: str
    connector_type: str
    event_type: str
    status: str
    retry_count: int
    max_retries: int
    error_message: str
    created_at: str
    updated_at: str
    sent_at: str


@dataclass(frozen=True)
class GateNotificationView:
    """Read-only projection of a GateNotification row for the grid."""

    id: str
    notification_type: str
    title: str
    body: str
    is_read: bool
    received_at: str


@dataclass(frozen=True)
class SyncSummaryView:
    """Aggregate counts displayed in the summary header."""

    pending_count: int
    failed_count: int
    sent_count: int
    total_count: int
    unread_notifications: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(value) -> str:
    """Format a datetime or None to a human-readable string."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _item_to_view(item: SyncQueueItem) -> SyncQueueItemView:
    return SyncQueueItemView(
        id=str(item.id),
        connector_type=item.connector_type or "",
        event_type=item.event_type or "",
        status=item.status or "",
        retry_count=item.retry_count or 0,
        max_retries=item.max_retries or 3,
        error_message=item.error_message or "",
        created_at=_fmt(item.created_at),
        updated_at=_fmt(item.updated_at),
        sent_at=_fmt(item.sent_at),
    )


def _notif_to_view(n: GateNotification) -> GateNotificationView:
    return GateNotificationView(
        id=str(n.id),
        notification_type=getattr(n, "notification_type", "") or "",
        title=getattr(n, "title", "") or "",
        body=getattr(n, "body", "") or "",
        is_read=bool(getattr(n, "is_read", False)),
        received_at=_fmt(getattr(n, "received_at", None)),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class SyncManagementService:
    """
    Business logic and data-access layer for the Data Sync and Backup module.

    Provides:
    - Outbox queue listing (pending / failed / sent) with optional filters.
    - Summary aggregates for the form header banner.
    - Reset-to-pending action for failed items.
    - Hard-delete for individual items or entire sent history.
    - GATE notification inbox listing.
    """

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> SyncSummaryView:
        """
        Return aggregate counts across all sync queue statuses.

        Returns:
            SyncSummaryView with pending, failed, sent, total counts and
            unread notification count.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                pending = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "pending"
                ).count()
                failed = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "failed"
                ).count()
                sent = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "sent"
                ).count()
                total = pending + failed + sent

                unread = 0
                if hasattr(GateNotification, "is_read"):
                    unread = session.query(GateNotification).filter(
                        GateNotification.is_read == False  # noqa: E712
                    ).count()

                return SyncSummaryView(
                    pending_count=pending,
                    failed_count=failed,
                    sent_count=sent,
                    total_count=total,
                    unread_notifications=unread,
                )
        except SQLAlchemyError:
            return SyncSummaryView(0, 0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Outbox queue listings
    # ------------------------------------------------------------------

    def list_pending(self, connector_type: str | None = None) -> list[SyncQueueItemView]:
        """
        Return pending outbox items ordered oldest-first.

        Args:
            connector_type: Optional filter on connector type.

        Returns:
            List of SyncQueueItemView.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                query = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "pending"
                )
                if connector_type:
                    query = query.filter(
                        SyncQueueItem.connector_type == connector_type
                    )
                rows = query.order_by(asc(SyncQueueItem.created_at)).all()
                return [_item_to_view(r) for r in rows]
        except SQLAlchemyError:
            return []

    def list_failed(self, connector_type: str | None = None) -> list[SyncQueueItemView]:
        """
        Return failed outbox items ordered newest-first.

        Args:
            connector_type: Optional filter on connector type.

        Returns:
            List of SyncQueueItemView.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                query = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "failed"
                )
                if connector_type:
                    query = query.filter(
                        SyncQueueItem.connector_type == connector_type
                    )
                rows = query.order_by(desc(SyncQueueItem.updated_at)).all()
                return [_item_to_view(r) for r in rows]
        except SQLAlchemyError:
            return []

    def list_sent(self, connector_type: str | None = None) -> list[SyncQueueItemView]:
        """
        Return successfully sent outbox items ordered newest-first.

        Args:
            connector_type: Optional filter on connector type.

        Returns:
            List of SyncQueueItemView.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                query = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "sent"
                )
                if connector_type:
                    query = query.filter(
                        SyncQueueItem.connector_type == connector_type
                    )
                rows = query.order_by(desc(SyncQueueItem.sent_at)).all()
                return [_item_to_view(r) for r in rows]
        except SQLAlchemyError:
            return []

    # ------------------------------------------------------------------
    # Outbox actions
    # ------------------------------------------------------------------

    def reset_to_pending(self, item_id: str) -> ServiceResult:
        """
        Reset a failed sync item to 'pending' so it will be retried.

        Args:
            item_id: UUID string of the SyncQueueItem to reset.

        Returns:
            ServiceResult with success flag and message.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                item = session.query(SyncQueueItem).filter(
                    SyncQueueItem.id == item_id
                ).first()
                if item is None:
                    return ServiceResult(False, "Sync item not found.")
                if item.status != "failed":
                    return ServiceResult(
                        False,
                        f"Only 'failed' items can be reset. Current status: {item.status}",
                    )
                item.status = "pending"
                item.retry_count = 0
                item.error_message = None
                session.commit()
                return ServiceResult(True, "Item reset to pending successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")

    def reset_all_failed(self, connector_type: str | None = None) -> ServiceResult:
        """
        Reset all failed items to 'pending'.

        Args:
            connector_type: If provided, only reset items for this connector.

        Returns:
            ServiceResult with success flag and count of reset items.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                query = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "failed"
                )
                if connector_type:
                    query = query.filter(
                        SyncQueueItem.connector_type == connector_type
                    )
                items = query.all()
                for item in items:
                    item.status = "pending"
                    item.retry_count = 0
                    item.error_message = None
                session.commit()
                count = len(items)
                return ServiceResult(True, f"{count} item(s) reset to pending.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")

    def delete_item(self, item_id: str) -> ServiceResult:
        """
        Hard-delete a single sync queue item by ID.

        Args:
            item_id: UUID string of the SyncQueueItem to delete.

        Returns:
            ServiceResult with success flag and message.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                item = session.query(SyncQueueItem).filter(
                    SyncQueueItem.id == item_id
                ).first()
                if item is None:
                    return ServiceResult(False, "Sync item not found.")
                session.delete(item)
                session.commit()
                return ServiceResult(True, "Sync item deleted.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")

    def clear_sent_history(self) -> ServiceResult:
        """
        Hard-delete all sent sync queue items.

        This is a maintenance operation to keep the outbox table lean.

        Returns:
            ServiceResult with success flag and count of deleted rows.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                rows = session.query(SyncQueueItem).filter(
                    SyncQueueItem.status == "sent"
                ).all()
                count = len(rows)
                for row in rows:
                    session.delete(row)
                session.commit()
                return ServiceResult(True, f"{count} sent record(s) cleared.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")

    # ------------------------------------------------------------------
    # GATE notification inbox
    # ------------------------------------------------------------------

    def list_notifications(self, unread_only: bool = False) -> list[GateNotificationView]:
        """
        Return GATE inbound notifications.

        Args:
            unread_only: If True, return only unread notifications.

        Returns:
            List of GateNotificationView ordered newest-first.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                query = session.query(GateNotification)
                if unread_only and hasattr(GateNotification, "is_read"):
                    query = query.filter(GateNotification.is_read == False)  # noqa: E712
                rows = query.order_by(
                    desc(GateNotification.received_at)
                ).all()
                return [_notif_to_view(r) for r in rows]
        except SQLAlchemyError:
            return []

    def mark_notification_read(self, notification_id: str) -> ServiceResult:
        """
        Mark a single GATE notification as read.

        Args:
            notification_id: UUID string of the GateNotification to mark.

        Returns:
            ServiceResult with success flag and message.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                notif = session.query(GateNotification).filter(
                    GateNotification.id == notification_id
                ).first()
                if notif is None:
                    return ServiceResult(False, "Notification not found.")
                if hasattr(notif, "is_read"):
                    notif.is_read = True
                session.commit()
                return ServiceResult(True, "Notification marked as read.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")

    def mark_all_notifications_read(self) -> ServiceResult:
        """
        Mark all unread GATE notifications as read.

        Returns:
            ServiceResult with success flag and count.
        """
        try:
            engine = Engine()
            with engine.get_session() as session:
                rows = session.query(GateNotification).all()
                count = 0
                for row in rows:
                    if hasattr(row, "is_read") and not row.is_read:
                        row.is_read = True
                        count += 1
                session.commit()
                return ServiceResult(True, f"{count} notification(s) marked as read.")
        except SQLAlchemyError as exc:
            return ServiceResult(False, f"Database error: {exc}")
