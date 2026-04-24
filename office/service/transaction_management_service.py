"""
Read-only service layer for the Transaction Management module.

Provides POS-grouped transaction queries across:
  TransactionHead      – completed transaction headers
  TransactionProduct   – product line items
  TransactionPayment   – payment records
  TransactionDiscount  – applied discounts
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import asc, desc

from data_layer.engine import Engine
from data_layer.model.definition.pos_terminal import PosTerminal
from data_layer.model.definition.transaction_discount import TransactionDiscount
from data_layer.model.definition.transaction_discount_type import TransactionDiscountType
from data_layer.model.definition.transaction_head import TransactionHead
from data_layer.model.definition.transaction_payment import TransactionPayment
from data_layer.model.definition.transaction_product import TransactionProduct


# ---------------------------------------------------------------------------
# View dataclasses (read-only projections)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PosTerminalSummary:
    """Minimal terminal identity used to build POS tabs."""

    id: str
    terminal_code: str
    terminal_name: str


@dataclass(frozen=True)
class TransactionHeadView:
    """Flattened transaction header row for the grid."""

    id: str
    transaction_unique_id: str
    pos_id: int
    transaction_date_time: str
    document_type: str
    transaction_type: str
    transaction_status: str
    receipt_number: int
    closure_number: int
    total_amount: str
    total_vat_amount: str
    total_discount_amount: str
    total_payment_amount: str
    total_change_amount: str
    base_currency: str
    order_source: str
    is_closed: bool
    is_cancel: bool


@dataclass(frozen=True)
class TransactionProductView:
    """Flattened product line item for the detail grid."""

    id: str
    line_no: int
    product_code: str
    product_name: str
    quantity: str
    unit_price: str
    unit_discount: str
    total_price: str
    total_vat: str
    vat_rate: str
    unit_of_measure: str
    is_voided: bool
    is_cancel: bool


@dataclass(frozen=True)
class TransactionPaymentView:
    """Flattened payment record for the detail grid."""

    id: str
    line_no: int
    payment_type: str
    payment_total: str
    currency_code: str
    currency_total: str
    payment_status: str
    payment_provider: str
    card_type: str
    card_number_masked: str
    authorization_code: str
    is_cancel: bool


@dataclass(frozen=True)
class TransactionDiscountView:
    """Flattened discount record for the detail grid."""

    id: str
    line_no: int
    discount_type_name: str
    discount_amount: str
    discount_rate: str
    discount_code: str
    is_cancel: bool


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class TransactionManagementService:
    """Read-only queries for transaction data grouped by POS terminal."""

    def __init__(self) -> None:
        self._engine = Engine()

    # ------------------------------------------------------------------
    # POS terminals
    # ------------------------------------------------------------------

    def list_pos_terminals(self) -> list[PosTerminalSummary]:
        """Return all registered POS terminals ordered by terminal code."""
        with self._engine.get_session() as session:
            rows = (
                session.query(PosTerminal)
                .order_by(asc(PosTerminal.terminal_code))
                .all()
            )
            return [
                PosTerminalSummary(
                    id=str(r.id),
                    terminal_code=r.terminal_code or "",
                    terminal_name=r.terminal_name or r.terminal_code or "",
                )
                for r in rows
            ]

    def list_distinct_pos_ids(self) -> list[int]:
        """Return distinct pos_id values that appear in transaction_head."""
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionHead.pos_id)
                .distinct()
                .order_by(asc(TransactionHead.pos_id))
                .all()
            )
            return [r.pos_id for r in rows if r.pos_id is not None]

    # ------------------------------------------------------------------
    # Transaction headers
    # ------------------------------------------------------------------

    def list_transactions(self, pos_id: int | None = None) -> list[TransactionHeadView]:
        """Return transaction headers, most recent first.

        When *pos_id* is provided only transactions from that terminal are
        returned; otherwise all terminals are included.
        """
        with self._engine.get_session() as session:
            query = session.query(TransactionHead)
            if pos_id is not None:
                query = query.filter(TransactionHead.pos_id == pos_id)
            rows = query.order_by(desc(TransactionHead.transaction_date_time)).all()

            result: list[TransactionHeadView] = []
            for r in rows:
                dt = r.transaction_date_time
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
                result.append(
                    TransactionHeadView(
                        id=str(r.id),
                        transaction_unique_id=r.transaction_unique_id or "",
                        pos_id=r.pos_id or 0,
                        transaction_date_time=dt_str,
                        document_type=r.document_type or "",
                        transaction_type=r.transaction_type or "",
                        transaction_status=r.transaction_status or "",
                        receipt_number=r.receipt_number or 0,
                        closure_number=r.closure_number or 0,
                        total_amount=f"{r.total_amount:.2f}" if r.total_amount is not None else "0.00",
                        total_vat_amount=f"{r.total_vat_amount:.2f}" if r.total_vat_amount is not None else "0.00",
                        total_discount_amount=f"{r.total_discount_amount:.2f}" if r.total_discount_amount is not None else "0.00",
                        total_payment_amount=f"{r.total_payment_amount:.2f}" if r.total_payment_amount is not None else "0.00",
                        total_change_amount=f"{r.total_change_amount:.2f}" if r.total_change_amount is not None else "0.00",
                        base_currency=r.base_currency or "",
                        order_source=r.order_source or "",
                        is_closed=bool(r.is_closed),
                        is_cancel=bool(r.is_cancel),
                    )
                )
            return result

    # ------------------------------------------------------------------
    # Transaction detail – products
    # ------------------------------------------------------------------

    def list_transaction_products(
        self, transaction_head_id: str
    ) -> list[TransactionProductView]:
        """Return product line items for the given transaction."""
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionProduct)
                .filter(TransactionProduct.fk_transaction_head_id == transaction_head_id)
                .order_by(asc(TransactionProduct.line_no))
                .all()
            )
            return [
                TransactionProductView(
                    id=str(r.id),
                    line_no=r.line_no or 0,
                    product_code=r.product_code or "",
                    product_name=r.product_name or "",
                    quantity=f"{r.quantity:.4f}" if r.quantity is not None else "0.0000",
                    unit_price=f"{r.unit_price:.4f}" if r.unit_price is not None else "0.0000",
                    unit_discount=f"{r.unit_discount:.4f}" if r.unit_discount is not None else "0.0000",
                    total_price=f"{r.total_price:.2f}" if r.total_price is not None else "0.00",
                    total_vat=f"{r.total_vat:.2f}" if r.total_vat is not None else "0.00",
                    vat_rate=f"{r.vat_rate:.2f}" if r.vat_rate is not None else "0.00",
                    unit_of_measure=r.unit_of_measure or "",
                    is_voided=bool(r.is_voided),
                    is_cancel=bool(r.is_cancel),
                )
                for r in rows
            ]

    # ------------------------------------------------------------------
    # Transaction detail – payments
    # ------------------------------------------------------------------

    def list_transaction_payments(
        self, transaction_head_id: str
    ) -> list[TransactionPaymentView]:
        """Return payment records for the given transaction."""
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionPayment)
                .filter(TransactionPayment.fk_transaction_head_id == transaction_head_id)
                .order_by(asc(TransactionPayment.line_no))
                .all()
            )
            return [
                TransactionPaymentView(
                    id=str(r.id),
                    line_no=r.line_no or 0,
                    payment_type=r.payment_type or "",
                    payment_total=f"{r.payment_total:.2f}" if r.payment_total is not None else "0.00",
                    currency_code=r.currency_code or "",
                    currency_total=f"{r.currency_total:.2f}" if r.currency_total is not None else "0.00",
                    payment_status=r.payment_status or "",
                    payment_provider=r.payment_provider or "",
                    card_type=r.card_type or "",
                    card_number_masked=r.card_number_masked or "",
                    authorization_code=r.authorization_code or "",
                    is_cancel=bool(r.is_cancel),
                )
                for r in rows
            ]

    # ------------------------------------------------------------------
    # Transaction detail – discounts
    # ------------------------------------------------------------------

    def list_transaction_discounts(
        self, transaction_head_id: str
    ) -> list[TransactionDiscountView]:
        """Return discount records for the given transaction."""
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionDiscount, TransactionDiscountType)
                .outerjoin(
                    TransactionDiscountType,
                    TransactionDiscount.fk_discount_type_id == TransactionDiscountType.id,
                )
                .filter(TransactionDiscount.fk_transaction_head_id == transaction_head_id)
                .order_by(asc(TransactionDiscount.line_no))
                .all()
            )
            return [
                TransactionDiscountView(
                    id=str(d.id),
                    line_no=d.line_no or 0,
                    discount_type_name=dt.name if dt else "",
                    discount_amount=f"{d.discount_amount:.2f}" if d.discount_amount is not None else "0.00",
                    discount_rate=f"{d.discount_rate:.2f}" if d.discount_rate is not None else "",
                    discount_code=d.discount_code or "",
                    is_cancel=bool(d.is_cancel),
                )
                for d, dt in rows
            ]
