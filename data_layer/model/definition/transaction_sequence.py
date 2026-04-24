"""
SaleFlex.OFFICE - Transaction Sequence Model

Tracks named sequence counters (e.g. ReceiptNumber, ClosureNumber) per POS
terminal so that OFFICE can maintain accurate sequence state for every
registered terminal independently.

Copyright (c) 2025 Ferhat Mousavi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
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