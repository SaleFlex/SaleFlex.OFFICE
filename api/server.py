"""
SaleFlex.OFFICE - REST API Server

Runs a lightweight Flask HTTP server in a background daemon thread so that
SaleFlex.PyPOS terminals can pull initialization data from and push completed
transactions to this OFFICE instance.

Endpoints
---------
GET  /api/v1/health
    Simple liveness check; always returns {"status": "ok"}.

GET  /api/v1/pos/init
    Returns all seed/reference data for a requesting POS terminal.
    Required query parameters: office_code, store_code, terminal_code

POST /api/v1/pos/transactions
    Accepts a batch of completed transaction records pushed by a PyPOS terminal.
    Body (JSON): {office_code, store_code, terminal_code, pos_id, transactions[],
                  sequences[{name, value}]}
    Response: {status, accepted, rejected}

POST /api/v1/pos/sequences
    Updates sequence counters for a specific POS terminal.
    Body (JSON): {office_code, store_code, terminal_code, pos_id,
                  sequences[{name, value}]}
    Response: {status, updated}
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request

from core.logger import get_logger
from data_layer.engine import Engine

logger = get_logger(__name__)

_flask_app = Flask(__name__)
_server_started = False
_server_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(records: list) -> list[dict]:
    """Convert a list of ORM objects to JSON-serialisable dicts via to_dict()."""
    return [r.to_dict() for r in records]


def _query_active(session, model_class):
    """
    Return all non-deleted records for *model_class*.
    Falls back to returning all records when the model has no is_deleted column.
    """
    query = session.query(model_class)
    if hasattr(model_class, "is_deleted"):
        query = query.filter(model_class.is_deleted == False)  # noqa: E712
    return query.all()


def _resolve_sequences_for_terminal(
    session,
    TransactionSequence,
    terminal_code: str,
) -> list:
    """
    Return the sequence rows that a PyPOS terminal should use on first boot.

    Priority order
    --------------
    1. Rows whose ``terminal_code`` matches this terminal exactly.
       These are present when the terminal has been used before and has already
       pushed its counters to OFFICE.  Restoring from these values lets a
       re-installed terminal continue from exactly where it left off.

    2. Rows where ``pos_id IS NULL`` (shared / store-wide defaults).
       These are the factory-default rows seeded during OFFICE initialisation
       (e.g. ReceiptNumber=1, ClosureNumber=1).  A brand-new terminal that has
       never pushed any data falls into this bucket.

    3. All active rows as a final fallback (legacy behaviour for databases that
       predate the per-terminal columns).
    """
    if terminal_code:
        terminal_rows = (
            session.query(TransactionSequence)
            .filter(
                TransactionSequence.terminal_code == terminal_code,
                TransactionSequence.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        if terminal_rows:
            return terminal_rows

    shared_rows = (
        session.query(TransactionSequence)
        .filter(
            TransactionSequence.pos_id.is_(None),
            TransactionSequence.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    if shared_rows:
        return shared_rows

    return _query_active(session, TransactionSequence)


def _build_init_payload(session, store, terminal_code: str = "") -> dict[str, Any]:
    """
    Query every table that a PyPOS terminal needs on first start-up and
    return the results as a flat dictionary keyed by table/resource name.

    Parameters
    ----------
    session:
        Active SQLAlchemy session.
    store:
        The validated Store ORM object for this request.
    terminal_code:
        The requesting terminal's unique code.  When provided, sequence
        counters are filtered to return terminal-specific values so that a
        re-installed POS continues from its last known counter values rather
        than starting from the store-wide defaults.
    """
    # Lazy imports keep the module importable before SQLAlchemy models load.
    from data_layer.model.definition.cashier import Cashier
    from data_layer.model.definition.country import Country
    from data_layer.model.definition.country_region import CountryRegion
    from data_layer.model.definition.city import City
    from data_layer.model.definition.district import District
    from data_layer.model.definition.currency import Currency
    from data_layer.model.definition.currency_table import CurrencyTable
    from data_layer.model.definition.payment_type import PaymentType
    from data_layer.model.definition.vat import Vat
    from data_layer.model.definition.product_unit import ProductUnit
    from data_layer.model.definition.product_manufacturer import ProductManufacturer
    from data_layer.model.definition.department_main_group import DepartmentMainGroup
    from data_layer.model.definition.department_sub_group import DepartmentSubGroup
    from data_layer.model.definition.product import Product
    from data_layer.model.definition.product_variant import ProductVariant
    from data_layer.model.definition.product_attribute import ProductAttribute
    from data_layer.model.definition.product_barcode import ProductBarcode
    from data_layer.model.definition.product_barcode_mask import ProductBarcodeMask
    from data_layer.model.definition.warehouse import Warehouse
    from data_layer.model.definition.warehouse_location import WarehouseLocation
    from data_layer.model.definition.warehouse_product_stock import WarehouseProductStock
    from data_layer.model.definition.transaction_discount_type import TransactionDiscountType
    from data_layer.model.definition.transaction_document_type import TransactionDocumentType
    from data_layer.model.definition.transaction_sequence import TransactionSequence
    from data_layer.model.definition.form import Form
    from data_layer.model.definition.form_control import FormControl
    from data_layer.model.definition.label_value import LabelValue
    from data_layer.model.definition.pos_settings import PosSettings
    from data_layer.model.definition.pos_virtual_keyboard import PosVirtualKeyboard
    from data_layer.model.definition.cashier_performance_target import CashierPerformanceTarget
    from data_layer.model.definition.campaign_type import CampaignType
    from data_layer.model.definition.campaign import Campaign
    from data_layer.model.definition.campaign_rule import CampaignRule
    from data_layer.model.definition.campaign_product import CampaignProduct
    from data_layer.model.definition.coupon import Coupon
    from data_layer.model.definition.loyalty_program import LoyaltyProgram
    from data_layer.model.definition.loyalty_tier import LoyaltyTier
    from data_layer.model.definition.loyalty_earn_rule import LoyaltyEarnRule
    from data_layer.model.definition.loyalty_redemption_policy import LoyaltyRedemptionPolicy
    from data_layer.model.definition.loyalty_program_policy import LoyaltyProgramPolicy
    from data_layer.model.definition.customer_segment import CustomerSegment
    from data_layer.model.definition.customer import Customer

    return {
        "cashiers":                  _serialize(_query_active(session, Cashier)),
        "countries":                 _serialize(session.query(Country).all()),
        "country_regions":           _serialize(_query_active(session, CountryRegion)),
        "store":                     store.to_dict(),
        "cities":                    _serialize(session.query(City).all()),
        "districts":                 _serialize(session.query(District).all()),
        "currencies":                _serialize(session.query(Currency).all()),
        "currency_table":            _serialize(session.query(CurrencyTable).all()),
        "payment_types":             _serialize(_query_active(session, PaymentType)),
        "vat_rates":                 _serialize(_query_active(session, Vat)),
        "product_units":             _serialize(_query_active(session, ProductUnit)),
        "product_manufacturers":     _serialize(_query_active(session, ProductManufacturer)),
        "department_main_groups":    _serialize(_query_active(session, DepartmentMainGroup)),
        "department_sub_groups":     _serialize(_query_active(session, DepartmentSubGroup)),
        "products":                  _serialize(_query_active(session, Product)),
        "product_variants":          _serialize(_query_active(session, ProductVariant)),
        "product_attributes":        _serialize(_query_active(session, ProductAttribute)),
        "product_barcodes":          _serialize(_query_active(session, ProductBarcode)),
        "product_barcode_masks":     _serialize(_query_active(session, ProductBarcodeMask)),
        "warehouses":                _serialize(_query_active(session, Warehouse)),
        "warehouse_locations":       _serialize(_query_active(session, WarehouseLocation)),
        "warehouse_product_stock":   _serialize(session.query(WarehouseProductStock).all()),
        "transaction_discount_types": _serialize(_query_active(session, TransactionDiscountType)),
        "transaction_document_types": _serialize(_query_active(session, TransactionDocumentType)),
        "transaction_sequences":     _serialize(
            _resolve_sequences_for_terminal(session, TransactionSequence, terminal_code)
        ),
        "forms":                     _serialize(_query_active(session, Form)),
        "form_controls":             _serialize(_query_active(session, FormControl)),
        "label_values":              _serialize(session.query(LabelValue).all()),
        "pos_settings":              _serialize(session.query(PosSettings).all()),
        "pos_virtual_keyboards":     _serialize(session.query(PosVirtualKeyboard).all()),
        "cashier_performance_targets": _serialize(_query_active(session, CashierPerformanceTarget)),
        "campaign_types":            _serialize(_query_active(session, CampaignType)),
        "campaigns":                 _serialize(_query_active(session, Campaign)),
        "campaign_rules":            _serialize(_query_active(session, CampaignRule)),
        "campaign_products":         _serialize(_query_active(session, CampaignProduct)),
        "coupons":                   _serialize(_query_active(session, Coupon)),
        "loyalty_programs":          _serialize(_query_active(session, LoyaltyProgram)),
        "loyalty_tiers":             _serialize(_query_active(session, LoyaltyTier)),
        "loyalty_earn_rules":        _serialize(_query_active(session, LoyaltyEarnRule)),
        "loyalty_redemption_policies": _serialize(_query_active(session, LoyaltyRedemptionPolicy)),
        "loyalty_program_policies":  _serialize(_query_active(session, LoyaltyProgramPolicy)),
        "customer_segments":         _serialize(_query_active(session, CustomerSegment)),
        "customers":                 _serialize(_query_active(session, Customer)),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@_flask_app.route("/api/v1/health", methods=["GET"])
def health():
    """Liveness check endpoint."""
    return jsonify({"status": "ok", "service": "SaleFlex.OFFICE"})


@_flask_app.route("/api/v1/pos/init", methods=["GET"])
def pos_init():
    """
    Return the full initialization data set for a POS terminal.

    Query parameters (all required):
      office_code   – identifies which OFFICE instance the terminal belongs to
      store_code    – identifies the store this terminal operates in
      terminal_code – uniquely identifies the terminal within the store
    """
    office_code   = request.args.get("office_code", "").strip()
    store_code    = request.args.get("store_code", "").strip()
    terminal_code = request.args.get("terminal_code", "").strip()

    if not office_code or not store_code or not terminal_code:
        return jsonify({
            "status": "error",
            "message": (
                "Missing required query parameters: "
                "office_code, store_code, terminal_code"
            ),
        }), 400

    try:
        from data_layer.model.definition.store import Store
        from data_layer.model.definition.pos_terminal import PosTerminal

        engine = Engine()
        with engine.get_session() as session:
            # Validate store ownership
            store = (
                session.query(Store)
                .filter(
                    Store.store_code == store_code,
                    Store.office_code == office_code,
                )
                .first()
            )
            if store is None:
                logger.warning(
                    "pos/init: store not found – office_code=%s store_code=%s",
                    office_code, store_code,
                )
                return jsonify({
                    "status": "error",
                    "message": (
                        f"No store found for office_code='{office_code}' "
                        f"and store_code='{store_code}'"
                    ),
                }), 404

            # Validate terminal registration
            terminal = (
                session.query(PosTerminal)
                .filter(
                    PosTerminal.fk_store_id == store.id,
                    PosTerminal.terminal_code == terminal_code,
                )
                .first()
            )
            if terminal is None:
                logger.warning(
                    "pos/init: terminal not found – terminal_code=%s store=%s",
                    terminal_code, store_code,
                )
                return jsonify({
                    "status": "error",
                    "message": (
                        f"Terminal '{terminal_code}' is not registered "
                        f"in store '{store_code}'"
                    ),
                }), 404

            if not terminal.is_allowed_pull:
                logger.warning(
                    "pos/init: pull not allowed for terminal_code=%s", terminal_code
                )
                return jsonify({
                    "status": "error",
                    "message": (
                        f"Terminal '{terminal_code}' is not authorised "
                        "to pull data from OFFICE"
                    ),
                }), 403

            # Build payload – pass terminal_code so sequences are filtered to
            # this terminal's previously pushed values (or fall back to defaults).
            data = _build_init_payload(session, store, terminal_code=terminal_code)

            # Record bootstrap timestamp
            terminal.last_bootstrap_at = datetime.now(timezone.utc)

            logger.info(
                "pos/init: data dispatched to terminal_code=%s store=%s "
                "(sequences: terminal-specific=%s)",
                terminal_code,
                store_code,
                any(
                    s.get("terminal_code") == terminal_code
                    for s in data.get("transaction_sequences", [])
                    if isinstance(s, dict)
                ),
            )
            return jsonify({
                "status": "ok",
                "office_code": office_code,
                "store_code": store_code,
                "terminal_code": terminal_code,
                "data": data,
            })

    except Exception as exc:
        logger.error("pos/init: unexpected error – %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Helpers – transaction ingestion
# ---------------------------------------------------------------------------


def _upsert_transaction_batch(session, transactions: list[dict]) -> tuple[int, int]:
    """
    Persist a list of serialised transaction dicts into the OFFICE database.

    Each transaction dict must contain at least a 'head' key with the
    TransactionHead fields.  Returns (accepted, rejected) counts.
    """
    from uuid import UUID
    from datetime import datetime
    from data_layer.model.definition.transaction_head import TransactionHead
    from data_layer.model.definition.transaction_product import TransactionProduct
    from data_layer.model.definition.transaction_payment import TransactionPayment
    from data_layer.model.definition.transaction_discount import TransactionDiscount
    from data_layer.model.definition.transaction_department import TransactionDepartment
    from data_layer.model.definition.transaction_tax import TransactionTax
    from data_layer.model.definition.transaction_tip import TransactionTip
    from data_layer.model.definition.transaction_surcharge import TransactionSurcharge
    from data_layer.model.definition.transaction_note import TransactionNote
    from data_layer.model.definition.transaction_loyalty import TransactionLoyalty
    from data_layer.model.definition.transaction_fiscal import TransactionFiscal
    from data_layer.model.definition.transaction_refund import TransactionRefund
    from data_layer.model.definition.transaction_change import TransactionChange
    from data_layer.model.definition.transaction_delivery import TransactionDelivery
    from data_layer.model.definition.transaction_kitchen_order import TransactionKitchenOrder

    # Map JSON key → (model class, FK field name)
    _LINE_MAP = [
        ("products",      TransactionProduct,     "fk_transaction_head_id"),
        ("payments",      TransactionPayment,      "fk_transaction_head_id"),
        ("discounts",     TransactionDiscount,     "fk_transaction_head_id"),
        ("departments",   TransactionDepartment,   "fk_transaction_head_id"),
        ("taxes",         TransactionTax,          "fk_transaction_head_id"),
        ("tips",          TransactionTip,          "fk_transaction_head_id"),
        ("surcharges",    TransactionSurcharge,    "fk_transaction_head_id"),
        ("notes",         TransactionNote,         "fk_transaction_head_id"),
        ("loyalty",       TransactionLoyalty,      "fk_transaction_head_id"),
        ("refunds",       TransactionRefund,       "fk_transaction_head_id"),
        ("changes",       TransactionChange,       "fk_transaction_head_id"),
        ("deliveries",    TransactionDelivery,     "fk_transaction_head_id"),
        ("kitchen_orders", TransactionKitchenOrder, "fk_transaction_head_id"),
    ]

    def _coerce(value, col_type_str: str):
        """Lightweight type coercion for incoming JSON values."""
        from datetime import date as _date
        if value is None:
            return None
        if "UUID" in col_type_str or col_type_str == "UUID":
            try:
                return UUID(str(value))
            except (ValueError, AttributeError):
                return value
        if "DateTime" in col_type_str or "DATETIME" in col_type_str.upper():
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                # Strip timezone suffix so we store naive datetimes
                v = value.split("+")[0].rstrip("Z").strip()
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ):
                    try:
                        return datetime.strptime(v, fmt)
                    except ValueError:
                        continue
        if col_type_str in ("Date", "DATE"):
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, _date):
                return value
            if isinstance(value, str):
                v = value[:10]
                try:
                    return datetime.strptime(v, "%Y-%m-%d").date()
                except ValueError:
                    pass
        return value

    def _apply_row(instance, data: dict, allowed_columns: set, col_types: dict):
        for key, val in data.items():
            if key not in allowed_columns:
                continue
            col_type_str = str(type(col_types.get(key, "")).__name__)
            instance.__dict__[key] = _coerce(val, col_type_str)

    accepted = rejected = 0

    for tx in transactions:
        try:
            head_data = tx.get("head", {})
            if not head_data:
                rejected += 1
                continue

            # Determine primary key for this head record
            raw_head_id = head_data.get("id")
            if not raw_head_id:
                rejected += 1
                continue
            try:
                head_uuid = UUID(str(raw_head_id))
            except (ValueError, AttributeError):
                rejected += 1
                continue

            # Check for an existing head by unique transaction id to avoid duplicates
            tx_unique_id = head_data.get("transaction_unique_id", "")
            existing = (
                session.query(TransactionHead)
                .filter(TransactionHead.transaction_unique_id == tx_unique_id)
                .first()
            ) if tx_unique_id else None

            if existing:
                # Already stored – skip the entire transaction
                accepted += 1
                continue

            # Build TransactionHead
            head_cols   = {c.name for c in TransactionHead.__table__.columns}
            head_ctypes = {c.name: c.type for c in TransactionHead.__table__.columns}
            head_obj = TransactionHead()
            _apply_row(head_obj, head_data, head_cols, head_ctypes)
            # Ensure primary key is set as UUID object
            head_obj.id = head_uuid
            session.add(head_obj)
            session.flush()

            # Build line items
            for key, model_cls, fk_field in _LINE_MAP:
                rows = tx.get(key, [])
                if key == "fiscal":
                    rows = [tx["fiscal"]] if tx.get("fiscal") else []
                if not rows:
                    continue
                line_cols   = {c.name for c in model_cls.__table__.columns}
                line_ctypes = {c.name: c.type for c in model_cls.__table__.columns}
                for row_data in rows:
                    if not row_data:
                        continue
                    line_obj = model_cls()
                    _apply_row(line_obj, row_data, line_cols, line_ctypes)
                    # Always point line items at the (possibly new) head UUID
                    setattr(line_obj, fk_field, head_uuid)
                    session.add(line_obj)

            session.flush()
            accepted += 1

        except Exception as exc:
            logger.error("_upsert_transaction_batch: row error – %s", exc)
            rejected += 1
            session.rollback()

    return accepted, rejected


def _upsert_sequences(
    session,
    pos_id: int,
    terminal_code: str,
    sequences: list[dict],
) -> int:
    """
    Upsert sequence counters for a specific POS terminal.

    For each (name, pos_id) pair: update the existing row's value and
    last_synced_at, or insert a new row if none exists.

    Returns the number of rows updated/inserted.
    """
    from datetime import datetime, timezone
    from data_layer.model.definition.transaction_sequence import TransactionSequence

    now = datetime.now(timezone.utc)
    updated = 0

    for seq in sequences:
        name = seq.get("name", "").strip()
        value = seq.get("value")
        if not name or value is None:
            continue
        try:
            value = int(value)
        except (TypeError, ValueError):
            continue

        existing = (
            session.query(TransactionSequence)
            .filter(
                TransactionSequence.name == name,
                TransactionSequence.pos_id == pos_id,
            )
            .first()
        )

        if existing:
            existing.value = value
            existing.terminal_code = terminal_code
            existing.last_synced_at = now
        else:
            row = TransactionSequence(
                name=name,
                value=value,
                pos_id=pos_id,
                terminal_code=terminal_code,
                last_synced_at=now,
            )
            session.add(row)

        updated += 1

    return updated


def _validate_terminal(session, office_code: str, store_code: str, terminal_code: str):
    """
    Validate the store and (optionally) the terminal against the OFFICE database.

    Store validation is strict: the (office_code, store_code) pair must match a
    known store; if not, a ValueError is raised and the request is rejected.

    Terminal validation is lenient: if the terminal_code is not found in the
    pos_terminal table a WARNING is logged, but the request is still accepted.
    This allows new or re-installed POS terminals to push data before an
    administrator has manually registered them in OFFICE.

    Returns (store, terminal_or_None).
    """
    from data_layer.model.definition.store import Store
    from data_layer.model.definition.pos_terminal import PosTerminal

    store = (
        session.query(Store)
        .filter(
            Store.store_code == store_code,
            Store.office_code == office_code,
        )
        .first()
    )
    if store is None:
        # Fall back: try matching only store_code in case office_code was not
        # set in the store record (e.g. database seeded before this field existed).
        store = (
            session.query(Store)
            .filter(Store.store_code == store_code)
            .first()
        )
        if store is None:
            raise ValueError(
                f"No store found for office_code='{office_code}' "
                f"and store_code='{store_code}'"
            )
        logger.warning(
            "_validate_terminal: store '%s' found but office_code mismatch "
            "(stored=%r, received=%r) – accepting with warning",
            store_code, getattr(store, "office_code", None), office_code,
        )

    terminal = None
    try:
        terminal = (
            session.query(PosTerminal)
            .filter(
                PosTerminal.fk_store_id == store.id,
                PosTerminal.terminal_code == terminal_code,
            )
            .first()
        )
    except Exception as exc:
        logger.warning(
            "_validate_terminal: could not query pos_terminal – %s "
            "(proceeding without terminal record)", exc,
        )

    if terminal is None:
        logger.warning(
            "_validate_terminal: terminal '%s' not found in store '%s' – "
            "accepting push from unregistered terminal",
            terminal_code, store_code,
        )

    return store, terminal


# ---------------------------------------------------------------------------
# Routes – new push endpoints
# ---------------------------------------------------------------------------


@_flask_app.route("/api/v1/pos/transactions", methods=["POST"])
def pos_receive_transactions():
    """
    Accept a batch of completed transaction records pushed by a PyPOS terminal.

    Body (JSON)
    -----------
    {
        "office_code":   "<code>",
        "store_code":    "<code>",
        "terminal_code": "<code>",
        "pos_id":        <int>,
        "transactions":  [ { "head": {...}, "products": [...], ... }, ... ],
        "sequences":     [ { "name": "<name>", "value": <int> }, ... ]
    }

    Response
    --------
    {"status": "ok", "accepted": <int>, "rejected": <int>}
    """
    body = request.get_json(silent=True) or {}
    office_code   = (body.get("office_code")   or "").strip()
    store_code    = (body.get("store_code")    or "").strip()
    terminal_code = (body.get("terminal_code") or "").strip()
    pos_id        = body.get("pos_id")
    transactions  = body.get("transactions", [])
    sequences     = body.get("sequences", [])

    if not office_code or not store_code or not terminal_code:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: office_code, store_code, terminal_code",
        }), 400

    if not isinstance(transactions, list):
        return jsonify({"status": "error", "message": "'transactions' must be a list"}), 400

    try:
        engine = Engine()
        with engine.get_session() as session:
            try:
                _validate_terminal(session, office_code, store_code, terminal_code)
            except ValueError as exc:
                logger.warning("pos/transactions: %s", exc)
                return jsonify({"status": "error", "message": str(exc)}), 404

            accepted, rejected = _upsert_transaction_batch(session, transactions)

            # Also update sequence counters if provided
            if sequences and pos_id is not None:
                _upsert_sequences(session, int(pos_id), terminal_code, sequences)

            session.commit()

        logger.info(
            "pos/transactions: terminal=%s accepted=%d rejected=%d",
            terminal_code, accepted, rejected,
        )
        return jsonify({"status": "ok", "accepted": accepted, "rejected": rejected})

    except Exception as exc:
        logger.error("pos/transactions: unexpected error – %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@_flask_app.route("/api/v1/pos/sequences", methods=["POST"])
def pos_update_sequences():
    """
    Update sequence counters for a specific POS terminal.

    Body (JSON)
    -----------
    {
        "office_code":   "<code>",
        "store_code":    "<code>",
        "terminal_code": "<code>",
        "pos_id":        <int>,
        "sequences":     [ { "name": "<name>", "value": <int> }, ... ]
    }

    Response
    --------
    {"status": "ok", "updated": <int>}
    """
    body = request.get_json(silent=True) or {}
    office_code   = (body.get("office_code")   or "").strip()
    store_code    = (body.get("store_code")    or "").strip()
    terminal_code = (body.get("terminal_code") or "").strip()
    pos_id        = body.get("pos_id")
    sequences     = body.get("sequences", [])

    if not office_code or not store_code or not terminal_code:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: office_code, store_code, terminal_code",
        }), 400

    if pos_id is None:
        return jsonify({"status": "error", "message": "Missing required field: pos_id"}), 400

    try:
        engine = Engine()
        with engine.get_session() as session:
            try:
                _validate_terminal(session, office_code, store_code, terminal_code)
            except ValueError as exc:
                logger.warning("pos/sequences: %s", exc)
                return jsonify({"status": "error", "message": str(exc)}), 404

            updated = _upsert_sequences(session, int(pos_id), terminal_code, sequences)
            session.commit()

        logger.info(
            "pos/sequences: terminal=%s updated=%d", terminal_code, updated
        )
        return jsonify({"status": "ok", "updated": updated})

    except Exception as exc:
        logger.error("pos/sequences: unexpected error – %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_api_server(
    host: str = "0.0.0.0",
    port: int = 9000,
    access_log: bool = False,
) -> threading.Thread:
    """
    Start the Flask REST API in a background daemon thread.

    The thread is a daemon so it is automatically terminated when the main
    PySide6 process exits.  Call this once during application startup.

    Parameters
    ----------
    host:
        Bind address (default ``"0.0.0.0"`` = all interfaces).
    port:
        TCP port to listen on.
    access_log:
        When ``True``, Werkzeug logs every incoming request to the
        application logger (INFO level).  Controlled by
        ``[network].access_log = true`` in ``settings.toml``.
        Defaults to ``False`` for quiet production runs.
    """
    global _server_started

    with _server_lock:
        if _server_started:
            logger.warning("REST API server is already running – skipping duplicate start")
            return threading.current_thread()  # type: ignore[return-value]

        def _run() -> None:
            werkzeug_logger = logging.getLogger("werkzeug")
            if access_log:
                # Mirror Werkzeug's output through the SaleFlex logger at INFO.
                werkzeug_logger.setLevel(logging.INFO)
                werkzeug_logger.propagate = True
            else:
                # Suppress Werkzeug access logs for quiet production output.
                werkzeug_logger.setLevel(logging.WARNING)
                werkzeug_logger.propagate = False

            _flask_app.run(
                host=host,
                port=port,
                use_reloader=False,
                threaded=True,
                debug=False,
            )

        thread = threading.Thread(target=_run, daemon=True, name="saleflex-office-api")
        thread.start()
        _server_started = True
        logger.info(
            "✓ REST API server started – listening on %s:%d  (access_log=%s)",
            host, port, access_log,
        )
        return thread
