"""
SaleFlex.OFFICE - POS Terminal Definition Model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UUID, UniqueConstraint
from sqlalchemy.sql import func
from uuid import uuid4

from data_layer.model.crud_model import Model
from data_layer.model.crud_model import CRUD
from data_layer.model.mixins import AuditMixin, SoftDeleteMixin


class PosTerminal(Model, CRUD, AuditMixin, SoftDeleteMixin):
    def __init__(
        self,
        fk_store_id=None,
        terminal_code=None,
        terminal_name=None,
        terminal_serial_no=None,
        ip_address=None,
        host_name=None,
        app_mode=None,
        software_version=None,
        is_active=True,
        is_online=False,
        is_allowed_pull=True,
        pull_interval_seconds=30,
    ):
        Model.__init__(self)
        CRUD.__init__(self)

        self.fk_store_id = fk_store_id
        self.terminal_code = terminal_code
        self.terminal_name = terminal_name
        self.terminal_serial_no = terminal_serial_no
        self.ip_address = ip_address
        self.host_name = host_name
        self.app_mode = app_mode
        self.software_version = software_version
        self.is_active = is_active
        self.is_online = is_online
        self.is_allowed_pull = is_allowed_pull
        self.pull_interval_seconds = pull_interval_seconds

    __tablename__ = "pos_terminal"
    __table_args__ = (
        UniqueConstraint("fk_store_id", "terminal_code", name="uq_pos_terminal_store_code"),
    )

    id = Column(UUID, primary_key=True, default=uuid4)
    fk_store_id = Column(UUID, ForeignKey("store.id"), nullable=False, index=True)

    terminal_code = Column(String(50), nullable=False)
    terminal_name = Column(String(100), nullable=True)
    terminal_serial_no = Column(String(100), nullable=True, unique=True)
    host_name = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)

    app_mode = Column(String(20), nullable=True)  # standalone | office | gate
    software_version = Column(String(30), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    is_online = Column(Boolean, nullable=False, default=False)
    is_allowed_pull = Column(Boolean, nullable=False, default=True)
    pull_interval_seconds = Column(Integer, nullable=False, default=30)

    last_bootstrap_at = Column(DateTime, nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<PosTerminal(store_id='{self.fk_store_id}', terminal_code='{self.terminal_code}', "
            f"is_online={self.is_online})>"
        )

