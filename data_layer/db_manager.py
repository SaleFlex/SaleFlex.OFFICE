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


def initialize_database() -> None:
    """Create database and seed data only for first startup."""
    engine = Engine()
    if engine.db_path.exists():
        _ensure_cashier_schema(engine)
        _ensure_form_schema(engine)
        return

    metadata.create_all(bind=engine.engine)
    _ensure_cashier_schema(engine)
    _ensure_form_schema(engine)
    insert_initial_data(engine=engine)

