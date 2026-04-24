"""
Transaction Models Initialization – SaleFlex.OFFICE

Transaction models in OFFICE are read-only mirrors of the data written by
SaleFlex.PyPOS terminals.  OFFICE never opens or creates in-progress
transactions, so temporary (draft) transaction tables are not needed here.

Permanent transaction models present in OFFICE (read-only):
  - TransactionHead            : Completed transaction header
  - TransactionProduct         : Product line items
  - TransactionPayment         : Payment records
  - TransactionChange          : Change/cash-return records
  - TransactionDelivery        : Delivery information
  - TransactionDiscount        : Applied discount records
  - TransactionDepartment      : Department totals per transaction
  - TransactionFiscal          : Fiscal compliance data
  - TransactionKitchenOrder    : Kitchen order tickets
  - TransactionLog             : Audit trail
  - TransactionLoyalty         : Loyalty program transactions
  - TransactionNote            : Transaction notes
  - TransactionRefund          : Refund records
  - TransactionSurcharge       : Surcharge records
  - TransactionTax             : Tax breakdown
  - TransactionTip             : Tip records
  - TransactionVoid            : Void records

All models are populated by PyPOS terminals; OFFICE only reads them.
"""


def _insert_transaction_placeholder(session):
    """Placeholder for transaction model initialization.

    No seed data is needed – transaction records are created exclusively by
    PyPOS terminals during live POS operations.
    """
    pass
