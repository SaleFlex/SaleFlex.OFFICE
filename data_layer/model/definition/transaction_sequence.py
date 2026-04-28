"""
SaleFlex.OFFICE - Transaction Sequence Model

Tracks named sequence counters (e.g. ReceiptNumber, ClosureNumber) per POS
terminal so that OFFICE can maintain accurate sequence state for every
registered terminal independently.
Copyright (C) 2025-2026 Mousavi.Tech

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from sqlalchemy import Column, Integer, String, DateTime, UUID, UniqueConstraint
from uuid import uuid4

from data_layer.model.crud_model import Model
from data_layer.model.crud_model import CRUD
from data_layer.model.mixins import AuditMixin, SoftDeleteMixin


class TransactionSequence(Model, CRUD, AuditMixin, SoftDeleteMixin):
    """
    Named sequence counter scoped to a specific POS terminal.

    Each row represents one counter (e.g. 'ReceiptNumber', 'ClosureNumber')
    for a particular POS terminal identified by pos_id / terminal_code.
    Rows with NULL pos_id are treated as shared / store-wide defaults.
    """

    def __init__(
        self,
        name=None,
        value: int = None,
        description=None,
        pos_id: int = None,
        terminal_code: str = None,
        last_synced_at=None,
    ):
        Model.__init__(self)
        CRUD.__init__(self)

        self.name = name
        self.value = value
        self.description = description
        self.pos_id = pos_id
        self.terminal_code = terminal_code
        self.last_synced_at = last_synced_at

    __tablename__ = "transaction_sequence"

    # A (name, pos_id) pair must be unique; NULL pos_id means store-wide default.
    __table_args__ = (
        UniqueConstraint("name", "pos_id", name="uq_sequence_name_pos"),
    )

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False)
    value = Column(Integer, nullable=False)
    description = Column(String(100), nullable=True)

    # POS terminal identity – populated when PyPOS pushes sequence updates.
    # NULL means the row was created as a shared store-wide counter (legacy).
    pos_id = Column(Integer, nullable=True, index=True)
    terminal_code = Column(String(50), nullable=True, index=True)

    # Timestamp of the most recent push from PyPOS terminal.
    last_synced_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<TransactionSequence(name='{self.name}', value='{self.value}', "
            f"pos_id={self.pos_id}, terminal_code='{self.terminal_code}')>"
        ) 