"""
Service layer for customer management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.customer import Customer
from data_layer.model.definition.customer_loyalty import CustomerLoyalty
from data_layer.model.definition.customer_segment import CustomerSegment
from data_layer.model.definition.customer_segment_member import CustomerSegmentMember
from data_layer.model.definition.loyalty_point_transaction import LoyaltyPointTransaction
from data_layer.model.definition.loyalty_program import LoyaltyProgram
from data_layer.model.definition.loyalty_tier import LoyaltyTier
from data_layer.model.definition.store import Store
from data_layer.model.definition.transaction_head import TransactionHead


@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str


@dataclass(frozen=True)
class LookupItem:
    id: str
    label: str


@dataclass(frozen=True)
class CustomerView:
    id: str
    name: str
    last_name: str
    email_address: str
    phone_number: str
    phone_normalized: str
    zip_code: str
    address_line_1: str
    address_line_2: str
    address_line_3: str
    date_of_birth: date | None
    gender: str
    national_id: str
    tax_id: str
    registration_source: str
    preferences_json: str
    description: str
    marketing_consent: bool
    sms_consent: bool
    email_consent: bool
    is_walkin: bool
    is_active: bool
    segment_count: int
    loyalty_available_points: int
    loyalty_program_name: str


@dataclass(frozen=True)
class CustomerSegmentView:
    id: str
    code: str
    name: str
    description: str
    segment_type: str
    criteria_json: str
    is_active: bool
    customer_count: int
    display_order: int
    color_code: str
    icon: str


@dataclass(frozen=True)
class CustomerSegmentMemberView:
    id: str
    customer_id: str
    customer_label: str
    customer_segment_id: str
    customer_segment_label: str
    assigned_date: datetime | None
    assigned_by: str
    assignment_reason: str
    is_active: bool


@dataclass(frozen=True)
class CustomerLoyaltyView:
    id: str
    customer_id: str
    customer_label: str
    loyalty_program_id: str
    loyalty_program_label: str
    loyalty_tier_id: str | None
    loyalty_tier_label: str
    loyalty_card_number: str
    total_points: int
    available_points: int
    lifetime_points: int
    points_to_expire: int
    points_expiry_date: date | None
    enrollment_date: datetime | None
    last_activity_date: datetime | None
    total_purchases: int
    total_spent: Decimal
    annual_spent: Decimal
    is_active: bool


@dataclass(frozen=True)
class LoyaltyPointTransactionView:
    id: str
    customer_loyalty_id: str
    customer_loyalty_label: str
    customer_id: str
    customer_label: str
    transaction_type: str
    points_amount: int
    balance_after: int
    transaction_head_id: str | None
    transaction_head_label: str
    store_id: str | None
    store_label: str
    cashier_id: str | None
    cashier_label: str
    transaction_date: datetime | None
    expiry_date: date | None
    reference_number: str
    description: str
    notes: str


@dataclass(frozen=True)
class CustomerOperationView:
    customer_id: str
    customer_name: str
    phone_number: str
    email_address: str
    segment_count: int
    segment_labels: str
    loyalty_program_name: str
    loyalty_tier_name: str
    available_points: int
    lifetime_points: int
    point_transaction_count: int
    last_point_transaction_at: datetime | None
    is_active: bool


class CustomerManagementService:
    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_customers(self, search_text: str | None = None) -> list[CustomerView]:
        with self._engine.get_session() as session:
            query = (
                session.query(Customer)
                .filter(Customer.is_deleted.is_(False))
                .order_by(asc(Customer.name), asc(Customer.last_name))
            )
            pattern_text = (search_text or "").strip()
            if pattern_text:
                pattern = f"%{pattern_text}%"
                query = query.filter(
                    Customer.name.ilike(pattern)
                    | Customer.last_name.ilike(pattern)
                    | Customer.phone_number.ilike(pattern)
                    | Customer.email_address.ilike(pattern)
                    | Customer.national_id.ilike(pattern)
                )
            customers = query.all()
            customer_ids = [row.id for row in customers]
            if not customer_ids:
                return []

            segment_rows = (
                session.query(
                    CustomerSegmentMember.fk_customer_id,
                    func.count(CustomerSegmentMember.id),
                )
                .filter(
                    CustomerSegmentMember.is_deleted.is_(False),
                    CustomerSegmentMember.is_active.is_(True),
                    CustomerSegmentMember.fk_customer_id.in_(customer_ids),
                )
                .group_by(CustomerSegmentMember.fk_customer_id)
                .all()
            )
            segment_count_map = {customer_id: int(count or 0) for customer_id, count in segment_rows}

            loyalty_rows = (
                session.query(CustomerLoyalty, LoyaltyProgram)
                .join(LoyaltyProgram, LoyaltyProgram.id == CustomerLoyalty.fk_loyalty_program_id)
                .filter(
                    CustomerLoyalty.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                    CustomerLoyalty.fk_customer_id.in_(customer_ids),
                )
                .all()
            )
            loyalty_map: dict[UUID, tuple[int, str]] = {}
            for loyalty, program in loyalty_rows:
                loyalty_map[loyalty.fk_customer_id] = (
                    int(loyalty.available_points or 0),
                    str(program.name or ""),
                )

            return [
                CustomerView(
                    id=str(row.id),
                    name=row.name,
                    last_name=row.last_name,
                    email_address=row.email_address or "",
                    phone_number=row.phone_number or "",
                    phone_normalized=row.phone_normalized or "",
                    zip_code=row.zip_code or "",
                    address_line_1=row.address_line_1 or "",
                    address_line_2=row.address_line_2 or "",
                    address_line_3=row.address_line_3 or "",
                    date_of_birth=row.date_of_birth,
                    gender=row.gender or "",
                    national_id=row.national_id or "",
                    tax_id=row.tax_id or "",
                    registration_source=row.registration_source or "",
                    preferences_json=row.preferences_json or "",
                    description=row.description or "",
                    marketing_consent=bool(row.marketing_consent),
                    sms_consent=bool(row.sms_consent),
                    email_consent=bool(row.email_consent),
                    is_walkin=bool(row.is_walkin),
                    is_active=bool(row.is_active),
                    segment_count=segment_count_map.get(row.id, 0),
                    loyalty_available_points=loyalty_map.get(row.id, (0, ""))[0],
                    loyalty_program_name=loyalty_map.get(row.id, (0, ""))[1],
                )
                for row in customers
            ]

    def save_customer(self, payload: dict[str, Any], customer_id: str | None = None) -> ServiceResult:
        first_name = str(payload.get("name", "")).strip()
        last_name = str(payload.get("last_name", "")).strip()
        phone_normalized = str(payload.get("phone_normalized", "")).strip()
        if not first_name or not last_name:
            return ServiceResult(False, "Customer name and last name are required.")

        try:
            with self._engine.get_session() as session:
                if phone_normalized:
                    existing_by_phone = (
                        session.query(Customer)
                        .filter(
                            Customer.phone_normalized == phone_normalized,
                            Customer.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if existing_by_phone and str(existing_by_phone.id) != str(customer_id):
                        return ServiceResult(False, "Phone normalized value is already in use.")

                if customer_id:
                    customer = (
                        session.query(Customer)
                        .filter(Customer.id == self._as_uuid(customer_id), Customer.is_deleted.is_(False))
                        .first()
                    )
                    if customer is None:
                        return ServiceResult(False, "Customer record not found.")
                else:
                    customer = Customer()
                    session.add(customer)

                customer.name = first_name
                customer.last_name = last_name
                customer.email_address = str(payload.get("email_address", "")).strip()
                customer.phone_number = str(payload.get("phone_number", "")).strip()
                customer.phone_normalized = phone_normalized or None
                customer.zip_code = str(payload.get("zip_code", "")).strip()
                customer.address_line_1 = str(payload.get("address_line_1", "")).strip()
                customer.address_line_2 = str(payload.get("address_line_2", "")).strip()
                customer.address_line_3 = str(payload.get("address_line_3", "")).strip()
                customer.gender = str(payload.get("gender", "")).strip() or None
                customer.national_id = str(payload.get("national_id", "")).strip()
                customer.tax_id = str(payload.get("tax_id", "")).strip()
                customer.registration_source = str(payload.get("registration_source", "")).strip()
                customer.preferences_json = str(payload.get("preferences_json", "")).strip()
                customer.description = str(payload.get("description", "")).strip()
                customer.marketing_consent = bool(payload.get("marketing_consent", False))
                customer.sms_consent = bool(payload.get("sms_consent", False))
                customer.email_consent = bool(payload.get("email_consent", False))
                customer.is_walkin = bool(payload.get("is_walkin", False))
                customer.is_active = bool(payload.get("is_active", True))
                customer.date_of_birth = self._parse_date(payload.get("date_of_birth"))

                return ServiceResult(
                    True,
                    "Customer updated successfully." if customer_id else "Customer created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Customer save operation failed due to a database error.")

    def delete_customer(self, customer_id: str) -> ServiceResult:
        return self._soft_delete(
            model=Customer,
            record_id=customer_id,
            not_found_message="Customer record not found.",
            success_message="Customer deleted successfully.",
            fail_message="Customer delete operation failed due to a database error.",
        )

    def list_customer_segments(self) -> list[CustomerSegmentView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(CustomerSegment)
                .filter(CustomerSegment.is_deleted.is_(False))
                .order_by(asc(CustomerSegment.display_order), asc(CustomerSegment.code))
                .all()
            )
            segment_ids = [row.id for row in rows]
            member_rows = (
                session.query(
                    CustomerSegmentMember.fk_customer_segment_id,
                    func.count(CustomerSegmentMember.id),
                )
                .filter(
                    CustomerSegmentMember.is_deleted.is_(False),
                    CustomerSegmentMember.is_active.is_(True),
                    CustomerSegmentMember.fk_customer_segment_id.in_(segment_ids),
                )
                .group_by(CustomerSegmentMember.fk_customer_segment_id)
                .all()
                if segment_ids
                else []
            )
            member_count_map = {segment_id: int(count or 0) for segment_id, count in member_rows}
            return [
                CustomerSegmentView(
                    id=str(row.id),
                    code=row.code,
                    name=row.name,
                    description=row.description or "",
                    segment_type=row.segment_type or "",
                    criteria_json=row.criteria_json or "",
                    is_active=bool(row.is_active),
                    customer_count=member_count_map.get(row.id, int(row.customer_count or 0)),
                    display_order=int(row.display_order or 0),
                    color_code=row.color_code or "",
                    icon=row.icon or "",
                )
                for row in rows
            ]

    def save_customer_segment(
        self,
        payload: dict[str, Any],
        segment_id: str | None = None,
    ) -> ServiceResult:
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        segment_type = str(payload.get("segment_type", "")).strip()
        if not code or not name or not segment_type:
            return ServiceResult(False, "Segment code, name, and type are required.")

        try:
            with self._engine.get_session() as session:
                existing_by_code = (
                    session.query(CustomerSegment)
                    .filter(CustomerSegment.code == code, CustomerSegment.is_deleted.is_(False))
                    .first()
                )
                if existing_by_code and str(existing_by_code.id) != str(segment_id):
                    return ServiceResult(False, f"Segment code '{code}' is already in use.")

                if segment_id:
                    segment = (
                        session.query(CustomerSegment)
                        .filter(
                            CustomerSegment.id == self._as_uuid(segment_id),
                            CustomerSegment.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if segment is None:
                        return ServiceResult(False, "Customer segment record not found.")
                else:
                    segment = CustomerSegment()
                    session.add(segment)

                segment.code = code
                segment.name = name
                segment.description = str(payload.get("description", "")).strip()
                segment.segment_type = segment_type
                segment.criteria_json = str(payload.get("criteria_json", "")).strip()
                segment.display_order = int(payload.get("display_order", 0) or 0)
                segment.color_code = str(payload.get("color_code", "")).strip()
                segment.icon = str(payload.get("icon", "")).strip()
                segment.is_active = bool(payload.get("is_active", True))

                return ServiceResult(
                    True,
                    "Customer segment updated successfully."
                    if segment_id
                    else "Customer segment created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Customer segment save operation failed due to a database error.")

    def delete_customer_segment(self, segment_id: str) -> ServiceResult:
        return self._soft_delete(
            model=CustomerSegment,
            record_id=segment_id,
            not_found_message="Customer segment record not found.",
            success_message="Customer segment deleted successfully.",
            fail_message="Customer segment delete operation failed due to a database error.",
        )

    def list_customer_segment_members(
        self,
        customer_id: str | None = None,
        segment_id: str | None = None,
    ) -> list[CustomerSegmentMemberView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CustomerSegmentMember, Customer, CustomerSegment)
                .join(Customer, Customer.id == CustomerSegmentMember.fk_customer_id)
                .join(CustomerSegment, CustomerSegment.id == CustomerSegmentMember.fk_customer_segment_id)
                .filter(
                    CustomerSegmentMember.is_deleted.is_(False),
                    Customer.is_deleted.is_(False),
                    CustomerSegment.is_deleted.is_(False),
                )
                .order_by(desc(CustomerSegmentMember.assigned_date))
            )
            if customer_id:
                query = query.filter(CustomerSegmentMember.fk_customer_id == self._as_uuid(customer_id))
            if segment_id:
                query = query.filter(CustomerSegmentMember.fk_customer_segment_id == self._as_uuid(segment_id))
            rows = query.all()
            return [
                CustomerSegmentMemberView(
                    id=str(member.id),
                    customer_id=str(member.fk_customer_id),
                    customer_label=f"{customer.name} {customer.last_name}".strip(),
                    customer_segment_id=str(member.fk_customer_segment_id),
                    customer_segment_label=f"{segment.code} - {segment.name}",
                    assigned_date=member.assigned_date,
                    assigned_by=member.assigned_by or "",
                    assignment_reason=member.assignment_reason or "",
                    is_active=bool(member.is_active),
                )
                for member, customer, segment in rows
            ]

    def save_customer_segment_member(
        self,
        payload: dict[str, Any],
        member_id: str | None = None,
    ) -> ServiceResult:
        customer_id = str(payload.get("customer_id", "")).strip()
        segment_id = str(payload.get("customer_segment_id", "")).strip()
        if not customer_id or not segment_id:
            return ServiceResult(False, "Customer and customer segment are required.")

        try:
            with self._engine.get_session() as session:
                if member_id:
                    member = (
                        session.query(CustomerSegmentMember)
                        .filter(
                            CustomerSegmentMember.id == self._as_uuid(member_id),
                            CustomerSegmentMember.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if member is None:
                        return ServiceResult(False, "Customer segment member record not found.")
                else:
                    duplicate = (
                        session.query(CustomerSegmentMember)
                        .filter(
                            CustomerSegmentMember.fk_customer_id == self._as_uuid(customer_id),
                            CustomerSegmentMember.fk_customer_segment_id == self._as_uuid(segment_id),
                            CustomerSegmentMember.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if duplicate:
                        return ServiceResult(False, "Selected customer is already in this segment.")
                    member = CustomerSegmentMember()
                    session.add(member)

                member.fk_customer_id = self._as_uuid(customer_id)
                member.fk_customer_segment_id = self._as_uuid(segment_id)
                member.assigned_date = self._parse_datetime(payload.get("assigned_date"), fallback_now=True)
                member.assigned_by = str(payload.get("assigned_by", "")).strip()
                member.assignment_reason = str(payload.get("assignment_reason", "")).strip()
                member.is_active = bool(payload.get("is_active", True))

                return ServiceResult(
                    True,
                    "Customer segment member updated successfully."
                    if member_id
                    else "Customer segment member created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Customer segment member save operation failed due to a database error.",
            )

    def delete_customer_segment_member(self, member_id: str) -> ServiceResult:
        return self._soft_delete(
            model=CustomerSegmentMember,
            record_id=member_id,
            not_found_message="Customer segment member record not found.",
            success_message="Customer segment member deleted successfully.",
            fail_message="Customer segment member delete operation failed due to a database error.",
        )

    def list_customer_loyalties(
        self,
        customer_id: str | None = None,
    ) -> list[CustomerLoyaltyView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CustomerLoyalty, Customer, LoyaltyProgram, LoyaltyTier)
                .join(Customer, Customer.id == CustomerLoyalty.fk_customer_id)
                .join(LoyaltyProgram, LoyaltyProgram.id == CustomerLoyalty.fk_loyalty_program_id)
                .outerjoin(LoyaltyTier, LoyaltyTier.id == CustomerLoyalty.fk_loyalty_tier_id)
                .filter(
                    CustomerLoyalty.is_deleted.is_(False),
                    Customer.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                )
                .order_by(asc(Customer.name), asc(Customer.last_name))
            )
            if customer_id:
                query = query.filter(CustomerLoyalty.fk_customer_id == self._as_uuid(customer_id))
            rows = query.all()
            return [
                CustomerLoyaltyView(
                    id=str(loyalty.id),
                    customer_id=str(loyalty.fk_customer_id),
                    customer_label=f"{customer.name} {customer.last_name}".strip(),
                    loyalty_program_id=str(loyalty.fk_loyalty_program_id),
                    loyalty_program_label=program.name,
                    loyalty_tier_id=str(loyalty.fk_loyalty_tier_id) if loyalty.fk_loyalty_tier_id else None,
                    loyalty_tier_label=tier.name if tier else "",
                    loyalty_card_number=loyalty.loyalty_card_number or "",
                    total_points=int(loyalty.total_points or 0),
                    available_points=int(loyalty.available_points or 0),
                    lifetime_points=int(loyalty.lifetime_points or 0),
                    points_to_expire=int(loyalty.points_to_expire or 0),
                    points_expiry_date=loyalty.points_expiry_date,
                    enrollment_date=loyalty.enrollment_date,
                    last_activity_date=loyalty.last_activity_date,
                    total_purchases=int(loyalty.total_purchases or 0),
                    total_spent=Decimal(str(loyalty.total_spent or 0)),
                    annual_spent=Decimal(str(loyalty.annual_spent or 0)),
                    is_active=bool(loyalty.is_active),
                )
                for loyalty, customer, program, tier in rows
            ]

    def save_customer_loyalty(
        self,
        payload: dict[str, Any],
        loyalty_id: str | None = None,
    ) -> ServiceResult:
        customer_id = str(payload.get("customer_id", "")).strip()
        program_id = str(payload.get("loyalty_program_id", "")).strip()
        if not customer_id or not program_id:
            return ServiceResult(False, "Customer and loyalty program are required.")

        try:
            with self._engine.get_session() as session:
                existing_by_customer = (
                    session.query(CustomerLoyalty)
                    .filter(
                        CustomerLoyalty.fk_customer_id == self._as_uuid(customer_id),
                        CustomerLoyalty.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_customer and str(existing_by_customer.id) != str(loyalty_id):
                    return ServiceResult(False, "Selected customer already has a loyalty profile.")

                card_number = str(payload.get("loyalty_card_number", "")).strip()
                if card_number:
                    existing_by_card = (
                        session.query(CustomerLoyalty)
                        .filter(
                            CustomerLoyalty.loyalty_card_number == card_number,
                            CustomerLoyalty.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if existing_by_card and str(existing_by_card.id) != str(loyalty_id):
                        return ServiceResult(False, "Loyalty card number is already in use.")

                if loyalty_id:
                    loyalty = (
                        session.query(CustomerLoyalty)
                        .filter(
                            CustomerLoyalty.id == self._as_uuid(loyalty_id),
                            CustomerLoyalty.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if loyalty is None:
                        return ServiceResult(False, "Customer loyalty record not found.")
                else:
                    loyalty = CustomerLoyalty()
                    session.add(loyalty)

                loyalty.fk_customer_id = self._as_uuid(customer_id)
                loyalty.fk_loyalty_program_id = self._as_uuid(program_id)
                loyalty.fk_loyalty_tier_id = self._as_uuid(payload.get("loyalty_tier_id"))
                loyalty.loyalty_card_number = card_number or None
                loyalty.total_points = int(payload.get("total_points", 0) or 0)
                loyalty.available_points = int(payload.get("available_points", 0) or 0)
                loyalty.lifetime_points = int(payload.get("lifetime_points", 0) or 0)
                loyalty.points_to_expire = int(payload.get("points_to_expire", 0) or 0)
                loyalty.points_expiry_date = self._parse_date(payload.get("points_expiry_date"))
                loyalty.enrollment_date = self._parse_datetime(payload.get("enrollment_date"), fallback_now=True)
                loyalty.last_activity_date = self._parse_datetime(payload.get("last_activity_date"))
                loyalty.total_purchases = int(payload.get("total_purchases", 0) or 0)
                loyalty.total_spent = Decimal(str(payload.get("total_spent", 0) or 0))
                loyalty.annual_spent = Decimal(str(payload.get("annual_spent", 0) or 0))
                loyalty.is_active = bool(payload.get("is_active", True))

                return ServiceResult(
                    True,
                    "Customer loyalty updated successfully."
                    if loyalty_id
                    else "Customer loyalty created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Customer loyalty save operation failed due to a database error.")

    def delete_customer_loyalty(self, loyalty_id: str) -> ServiceResult:
        return self._soft_delete(
            model=CustomerLoyalty,
            record_id=loyalty_id,
            not_found_message="Customer loyalty record not found.",
            success_message="Customer loyalty deleted successfully.",
            fail_message="Customer loyalty delete operation failed due to a database error.",
        )

    def list_loyalty_point_transactions(
        self,
        customer_id: str | None = None,
        customer_loyalty_id: str | None = None,
    ) -> list[LoyaltyPointTransactionView]:
        with self._engine.get_session() as session:
            query = (
                session.query(
                    LoyaltyPointTransaction,
                    CustomerLoyalty,
                    Customer,
                    Cashier,
                    Store,
                    TransactionHead,
                )
                .join(CustomerLoyalty, CustomerLoyalty.id == LoyaltyPointTransaction.fk_customer_loyalty_id)
                .join(Customer, Customer.id == LoyaltyPointTransaction.fk_customer_id)
                .outerjoin(Cashier, Cashier.id == LoyaltyPointTransaction.fk_cashier_id)
                .outerjoin(Store, Store.id == LoyaltyPointTransaction.fk_store_id)
                .outerjoin(TransactionHead, TransactionHead.id == LoyaltyPointTransaction.fk_transaction_head_id)
                .filter(
                    LoyaltyPointTransaction.is_deleted.is_(False),
                    CustomerLoyalty.is_deleted.is_(False),
                    Customer.is_deleted.is_(False),
                )
                .order_by(desc(LoyaltyPointTransaction.transaction_date))
            )
            if customer_id:
                query = query.filter(LoyaltyPointTransaction.fk_customer_id == self._as_uuid(customer_id))
            if customer_loyalty_id:
                query = query.filter(
                    LoyaltyPointTransaction.fk_customer_loyalty_id == self._as_uuid(customer_loyalty_id)
                )
            rows = query.all()
            return [
                LoyaltyPointTransactionView(
                    id=str(txn.id),
                    customer_loyalty_id=str(txn.fk_customer_loyalty_id),
                    customer_loyalty_label=(
                        loyalty.loyalty_card_number
                        or f"{customer.name} {customer.last_name}".strip()
                    ),
                    customer_id=str(txn.fk_customer_id),
                    customer_label=f"{customer.name} {customer.last_name}".strip(),
                    transaction_type=txn.transaction_type,
                    points_amount=int(txn.points_amount or 0),
                    balance_after=int(txn.balance_after or 0),
                    transaction_head_id=str(txn.fk_transaction_head_id) if txn.fk_transaction_head_id else None,
                    transaction_head_label=(txn_head.transaction_unique_id if txn_head else ""),
                    store_id=str(txn.fk_store_id) if txn.fk_store_id else None,
                    store_label=(store.store_code if store else ""),
                    cashier_id=str(txn.fk_cashier_id) if txn.fk_cashier_id else None,
                    cashier_label=(
                        f"{cashier.no} - {cashier.user_name}" if cashier else ""
                    ),
                    transaction_date=txn.transaction_date,
                    expiry_date=txn.expiry_date,
                    reference_number=txn.reference_number or "",
                    description=txn.description or "",
                    notes=txn.notes or "",
                )
                for txn, loyalty, customer, cashier, store, txn_head in rows
            ]

    def save_loyalty_point_transaction(
        self,
        payload: dict[str, Any],
        transaction_id: str | None = None,
    ) -> ServiceResult:
        customer_loyalty_id = str(payload.get("customer_loyalty_id", "")).strip()
        customer_id = str(payload.get("customer_id", "")).strip()
        transaction_type = str(payload.get("transaction_type", "")).strip()
        if not customer_loyalty_id or not customer_id or not transaction_type:
            return ServiceResult(
                False,
                "Customer loyalty, customer, and transaction type are required.",
            )

        try:
            with self._engine.get_session() as session:
                if transaction_id:
                    txn = (
                        session.query(LoyaltyPointTransaction)
                        .filter(
                            LoyaltyPointTransaction.id == self._as_uuid(transaction_id),
                            LoyaltyPointTransaction.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if txn is None:
                        return ServiceResult(False, "Loyalty point transaction record not found.")
                else:
                    txn = LoyaltyPointTransaction()
                    session.add(txn)

                points_amount = int(payload.get("points_amount", 0) or 0)
                balance_after_raw = payload.get("balance_after")
                balance_after = (
                    int(balance_after_raw)
                    if str(balance_after_raw or "").strip()
                    else int(payload.get("available_points_hint", 0) or 0) + points_amount
                )

                txn.fk_customer_loyalty_id = self._as_uuid(customer_loyalty_id)
                txn.fk_customer_id = self._as_uuid(customer_id)
                txn.transaction_type = transaction_type
                txn.points_amount = points_amount
                txn.balance_after = balance_after
                txn.fk_transaction_head_id = self._as_uuid(payload.get("transaction_head_id"))
                txn.fk_store_id = self._as_uuid(payload.get("store_id"))
                txn.fk_cashier_id = self._as_uuid(payload.get("cashier_id"))
                txn.transaction_date = self._parse_datetime(payload.get("transaction_date"), fallback_now=True)
                txn.expiry_date = self._parse_date(payload.get("expiry_date"))
                txn.reference_number = str(payload.get("reference_number", "")).strip()
                txn.description = str(payload.get("description", "")).strip()
                txn.notes = str(payload.get("notes", "")).strip()

                loyalty = (
                    session.query(CustomerLoyalty)
                    .filter(
                        CustomerLoyalty.id == self._as_uuid(customer_loyalty_id),
                        CustomerLoyalty.is_deleted.is_(False),
                    )
                    .first()
                )
                if loyalty:
                    loyalty.available_points = balance_after
                    loyalty.total_points = max(balance_after, int(loyalty.total_points or 0))
                    loyalty.last_activity_date = txn.transaction_date

                return ServiceResult(
                    True,
                    "Loyalty point transaction updated successfully."
                    if transaction_id
                    else "Loyalty point transaction created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Loyalty point transaction save operation failed due to a database error.",
            )

    def delete_loyalty_point_transaction(self, transaction_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyPointTransaction,
            record_id=transaction_id,
            not_found_message="Loyalty point transaction record not found.",
            success_message="Loyalty point transaction deleted successfully.",
            fail_message="Loyalty point transaction delete operation failed due to a database error.",
        )

    def list_customer_operations(
        self,
        customer_id: str | None = None,
        segment_id: str | None = None,
        active_only: bool = False,
    ) -> list[CustomerOperationView]:
        with self._engine.get_session() as session:
            customer_query = (
                session.query(Customer, CustomerLoyalty, LoyaltyProgram, LoyaltyTier)
                .outerjoin(
                    CustomerLoyalty,
                    (CustomerLoyalty.fk_customer_id == Customer.id)
                    & CustomerLoyalty.is_deleted.is_(False),
                )
                .outerjoin(LoyaltyProgram, LoyaltyProgram.id == CustomerLoyalty.fk_loyalty_program_id)
                .outerjoin(LoyaltyTier, LoyaltyTier.id == CustomerLoyalty.fk_loyalty_tier_id)
                .filter(Customer.is_deleted.is_(False))
                .order_by(asc(Customer.name), asc(Customer.last_name))
            )
            if customer_id:
                customer_query = customer_query.filter(Customer.id == self._as_uuid(customer_id))
            if active_only:
                customer_query = customer_query.filter(Customer.is_active.is_(True))
            base_rows = customer_query.all()
            if not base_rows:
                return []

            customer_ids = [customer.id for customer, *_ in base_rows]
            member_query = (
                session.query(CustomerSegmentMember, CustomerSegment)
                .join(CustomerSegment, CustomerSegment.id == CustomerSegmentMember.fk_customer_segment_id)
                .filter(
                    CustomerSegmentMember.is_deleted.is_(False),
                    CustomerSegmentMember.is_active.is_(True),
                    CustomerSegment.is_deleted.is_(False),
                    CustomerSegmentMember.fk_customer_id.in_(customer_ids),
                )
            )
            if segment_id:
                member_query = member_query.filter(
                    CustomerSegmentMember.fk_customer_segment_id == self._as_uuid(segment_id)
                )
            members = member_query.all()

            segment_labels_map: dict[UUID, list[str]] = {}
            for member, segment in members:
                segment_labels_map.setdefault(member.fk_customer_id, []).append(segment.name)

            point_txn_rows = (
                session.query(
                    LoyaltyPointTransaction.fk_customer_id,
                    func.count(LoyaltyPointTransaction.id),
                    func.max(LoyaltyPointTransaction.transaction_date),
                )
                .filter(
                    LoyaltyPointTransaction.is_deleted.is_(False),
                    LoyaltyPointTransaction.fk_customer_id.in_(customer_ids),
                )
                .group_by(LoyaltyPointTransaction.fk_customer_id)
                .all()
            )
            point_txn_map = {
                customer_fk: (int(count or 0), last_date)
                for customer_fk, count, last_date in point_txn_rows
            }

            result: list[CustomerOperationView] = []
            for customer, loyalty, program, tier in base_rows:
                segments = segment_labels_map.get(customer.id, [])
                if segment_id and not segments:
                    continue
                tx_count, last_txn_at = point_txn_map.get(customer.id, (0, None))
                result.append(
                    CustomerOperationView(
                        customer_id=str(customer.id),
                        customer_name=f"{customer.name} {customer.last_name}".strip(),
                        phone_number=customer.phone_number or "",
                        email_address=customer.email_address or "",
                        segment_count=len(segments),
                        segment_labels=", ".join(sorted(segments)),
                        loyalty_program_name=program.name if program else "",
                        loyalty_tier_name=tier.name if tier else "",
                        available_points=int(loyalty.available_points or 0) if loyalty else 0,
                        lifetime_points=int(loyalty.lifetime_points or 0) if loyalty else 0,
                        point_transaction_count=tx_count,
                        last_point_transaction_at=last_txn_at,
                        is_active=bool(customer.is_active),
                    )
                )
            return result

    def list_customer_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=row.label)
            for row in self._generic_lookup(
                model=Customer,
                order_columns=(asc(Customer.name), asc(Customer.last_name)),
                build_label=lambda row: f"{row.name} {row.last_name}".strip(),
            )
        ]

    def list_customer_segment_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=row.label)
            for row in self._generic_lookup(
                model=CustomerSegment,
                order_columns=(asc(CustomerSegment.display_order), asc(CustomerSegment.code)),
                build_label=lambda row: f"{row.code} - {row.name}",
            )
        ]

    def list_loyalty_program_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(LoyaltyProgram)
                .filter(LoyaltyProgram.is_deleted.is_(False))
                .order_by(desc(LoyaltyProgram.is_active), asc(LoyaltyProgram.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.name) for row in rows]

    def list_loyalty_tier_lookups(self, program_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyTier)
                .filter(LoyaltyTier.is_deleted.is_(False))
                .order_by(asc(LoyaltyTier.tier_level), asc(LoyaltyTier.name))
            )
            if program_id:
                query = query.filter(LoyaltyTier.fk_loyalty_program_id == self._as_uuid(program_id))
            rows = query.all()
            return [LookupItem(id=str(row.id), label=f"L{row.tier_level} - {row.name}") for row in rows]

    def list_customer_loyalty_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(CustomerLoyalty, Customer)
                .join(Customer, Customer.id == CustomerLoyalty.fk_customer_id)
                .filter(CustomerLoyalty.is_deleted.is_(False), Customer.is_deleted.is_(False))
                .order_by(asc(Customer.name), asc(Customer.last_name))
                .all()
            )
            return [
                LookupItem(
                    id=str(loyalty.id),
                    label=(
                        loyalty.loyalty_card_number
                        or f"{customer.name} {customer.last_name}".strip()
                    ),
                )
                for loyalty, customer in rows
            ]

    def list_store_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Store)
                .filter(Store.is_deleted.is_(False))
                .order_by(asc(Store.store_code))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.store_code or "-") for row in rows]

    def list_cashier_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Cashier)
                .filter(Cashier.is_deleted.is_(False))
                .order_by(asc(Cashier.no))
                .all()
            )
            return [LookupItem(id=str(row.id), label=f"{row.no} - {row.user_name}") for row in rows]

    def list_transaction_head_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionHead)
                .filter(TransactionHead.is_deleted.is_(False))
                .order_by(desc(TransactionHead.transaction_date_time))
                .limit(250)
                .all()
            )
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.transaction_unique_id} ({row.transaction_date_time.isoformat(sep=' ')})",
                )
                for row in rows
            ]

    @staticmethod
    def _as_uuid(value: str | UUID | None) -> UUID | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        normalized = str(value).strip()
        if not normalized:
            return None
        return UUID(normalized)

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        return datetime.strptime(raw, "%Y-%m-%d").date()

    @staticmethod
    def _parse_datetime(value: Any, fallback_now: bool = False) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return datetime.now() if fallback_now else None
        if "T" in raw:
            return datetime.fromisoformat(raw)
        if len(raw) == 16:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return datetime.fromisoformat(raw)

    def _resolve_default_store_id(self) -> str | None:
        with self._engine.get_session() as session:
            store = (
                session.query(Store)
                .filter(Store.store_code == self._store_code, Store.is_deleted.is_(False))
                .first()
            )
            if store is None:
                store = (
                    session.query(Store)
                    .filter(Store.is_deleted.is_(False))
                    .order_by(asc(Store.store_code))
                    .first()
                )
            return str(store.id) if store else None

    def _generic_lookup(
        self,
        model: Any,
        order_columns: tuple[Any, ...],
        build_label: Any,
    ) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(model)
                .filter(model.is_deleted.is_(False))
                .order_by(*order_columns)
                .all()
            )
            return [LookupItem(id=str(row.id), label=str(build_label(row))) for row in rows]

    def _soft_delete(
        self,
        model: Any,
        record_id: str,
        not_found_message: str,
        success_message: str,
        fail_message: str,
    ) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                row = (
                    session.query(model)
                    .filter(model.id == self._as_uuid(record_id), model.is_deleted.is_(False))
                    .first()
                )
                if row is None:
                    return ServiceResult(False, not_found_message)
                row.is_deleted = True
                return ServiceResult(True, success_message)
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, fail_message)
