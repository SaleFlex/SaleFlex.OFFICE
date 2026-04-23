"""
SaleFlex.OFFICE - REST API Server

Runs a lightweight Flask HTTP server in a background daemon thread so that
SaleFlex.PyPOS terminals can pull initialization and reference data from
this OFFICE instance when operating in 'office' mode.

Endpoints
---------
GET /api/v1/pos/init
    Returns all seed/reference data for a requesting POS terminal.
    Required query parameters: office_code, store_code, terminal_code

GET /api/v1/health
    Simple liveness check; always returns {"status": "ok"}.
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


def _build_init_payload(session, store) -> dict[str, Any]:
    """
    Query every table that a PyPOS terminal needs on first start-up and
    return the results as a flat dictionary keyed by table/resource name.
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
        "transaction_sequences":     _serialize(_query_active(session, TransactionSequence)),
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

            # Build payload
            data = _build_init_payload(session, store)

            # Record bootstrap timestamp
            terminal.last_bootstrap_at = datetime.now(timezone.utc)

            logger.info(
                "pos/init: data dispatched to terminal_code=%s store=%s",
                terminal_code, store_code,
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
