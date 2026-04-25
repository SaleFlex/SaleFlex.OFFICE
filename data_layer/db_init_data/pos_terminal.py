"""
SaleFlex.OFFICE - Database Initial Data (POS terminal)
"""

from data_layer.model.definition.pos_terminal import PosTerminal

from core.logger import get_logger

logger = get_logger(__name__)


def _insert_default_pos_terminal(session, store_id, admin_cashier_id=None) -> PosTerminal:
    """Insert one default POS terminal in the store if not exists."""
    terminal_exists = (
        session.query(PosTerminal)
        .filter_by(fk_store_id=store_id, terminal_code="POS-001", is_deleted=False)
        .first()
    )
    if terminal_exists:
        logger.info("✓ Default POS terminal already exists")
        return terminal_exists

    terminal = PosTerminal(
        fk_store_id=store_id,
        terminal_code="POS-001",
        terminal_name="Main POS Terminal",
        terminal_serial_no="SFS-OFFICE-POS-001",
        ip_address="127.0.0.1",
        host_name="LOCAL-POS-001",
        app_mode="office",
        software_version="0.1.0a2",
        is_active=True,
        is_online=False,
        is_allowed_pull=True,
        pull_interval_seconds=30,
    )
    if admin_cashier_id is not None:
        terminal.fk_cashier_create_id = admin_cashier_id
        terminal.fk_cashier_update_id = admin_cashier_id

    session.add(terminal)
    session.flush()
    logger.info("✓ Default POS terminal added (POS-001)")
    return terminal

