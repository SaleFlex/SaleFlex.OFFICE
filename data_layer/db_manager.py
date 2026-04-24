"""Database bootstrap helpers for SaleFlex.OFFICE."""

import data_layer.model.definition  # noqa: F401
from data_layer.db_init_data import insert_initial_data
from data_layer.engine import Engine
from data_layer.model import metadata


def _ensure_cashier_schema(engine: Engine) -> None:
    """Apply lightweight cashier table migrations required by current models."""
    with engine.engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(cashier)").fetchall()
        }
        if columns and "is_manager" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE cashier ADD COLUMN is_manager BOOLEAN NOT NULL DEFAULT 0"
            )


def _ensure_form_schema(engine: Engine) -> None:
    """Apply lightweight form table migrations required by current models."""
    with engine.engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(form)").fetchall()
        }
        if not columns:
            return
        if "is_shared_across_pos" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE form ADD COLUMN is_shared_across_pos BOOLEAN NOT NULL DEFAULT 1"
            )
        if "fk_pos_terminal_id" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE form ADD COLUMN fk_pos_terminal_id UUID"
            )


def _ensure_transaction_sequence_schema(engine: Engine) -> None:
    """
    Add POS-scoped columns to the transaction_sequence table.

    Older databases only have (id, name, value, description) plus audit/soft-delete
    columns.  This migration adds:
      - pos_id         INTEGER  NULL  – identifies the originating POS terminal
      - terminal_code  TEXT     NULL  – human-readable terminal code
      - last_synced_at DATETIME NULL  – timestamp of the most recent PyPOS push
    """
    with engine.engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(transaction_sequence)"
            ).fetchall()
        }
        if not columns:
            return
        if "pos_id" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE transaction_sequence ADD COLUMN pos_id INTEGER"
            )
        if "terminal_code" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE transaction_sequence ADD COLUMN terminal_code VARCHAR(50)"
            )
        if "last_synced_at" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE transaction_sequence ADD COLUMN last_synced_at DATETIME"
            )


def _ensure_pos_terminal_default(engine: Engine) -> None:
    """
    Ensure that at least one POS terminal record exists.

    This is a data-level migration that runs on every startup (both new and
    existing databases).  It is idempotent: if any terminal record already
    exists the function returns immediately.

    This guarantees that the first PyPOS terminal connecting in 'office' mode
    can push transactions even before an administrator has manually registered
    a terminal through the OFFICE UI.
    """
    from data_layer.model.definition.pos_terminal import PosTerminal
    from data_layer.model.definition.store import Store

    try:
        with engine.get_session() as session:
            terminal_count = session.query(PosTerminal).count()
            if terminal_count > 0:
                return

            # Resolve the first active store to attach the default terminal to.
            store = (
                session.query(Store)
                .filter(Store.is_active == True)  # noqa: E712
                .first()
            )
            if store is None:
                return

            terminal = PosTerminal(
                fk_store_id=store.id,
                terminal_code="POS-001",
                terminal_name="Main POS Terminal",
                terminal_serial_no="SFS-OFFICE-POS-001",
                ip_address="127.0.0.1",
                host_name="LOCAL-POS-001",
                app_mode="office",
                software_version="0.1.0-alpha",
                is_active=True,
                is_online=False,
                is_allowed_pull=True,
                pull_interval_seconds=30,
            )
            session.add(terminal)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "_ensure_pos_terminal_default: could not create default terminal – %s", exc
        )


def initialize_database() -> None:
    """Create database and seed data only for first startup."""
    engine = Engine()
    if engine.db_path.exists():
        _ensure_cashier_schema(engine)
        _ensure_form_schema(engine)
        _ensure_transaction_sequence_schema(engine)
        _ensure_pos_terminal_default(engine)
        return

    metadata.create_all(bind=engine.engine)
    _ensure_cashier_schema(engine)
    _ensure_form_schema(engine)
    _ensure_transaction_sequence_schema(engine)
    insert_initial_data(engine=engine)
    _ensure_pos_terminal_default(engine)

