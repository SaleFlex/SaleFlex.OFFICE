"""
Service layer for campaign management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.campaign import Campaign
from data_layer.model.definition.campaign_product import CampaignProduct
from data_layer.model.definition.campaign_rule import CampaignRule
from data_layer.model.definition.campaign_type import CampaignType
from data_layer.model.definition.campaign_usage import CampaignUsage
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.customer import Customer
from data_layer.model.definition.customer_segment import CustomerSegment
from data_layer.model.definition.department_main_group import DepartmentMainGroup
from data_layer.model.definition.payment_type import PaymentType
from data_layer.model.definition.product import Product
from data_layer.model.definition.product_manufacturer import ProductManufacturer
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
class CampaignView:
    id: str
    code: str
    name: str
    description: str
    fk_campaign_type_id: str
    campaign_type_name: str
    fk_store_id: str | None
    store_label: str
    discount_type: str
    discount_value: Decimal
    discount_percentage: Decimal
    max_discount_amount: Decimal
    min_purchase_amount: Decimal
    max_purchase_amount: Decimal
    buy_quantity: int
    get_quantity: int
    start_date: datetime | None
    end_date: datetime | None
    start_time: time | None
    end_time: time | None
    days_of_week: str
    priority: int
    is_combinable: bool
    usage_limit_per_customer: int | None
    total_usage_limit: int | None
    total_usage_count: int
    is_active: bool
    is_auto_apply: bool
    requires_coupon: bool
    fk_customer_segment_id: str | None
    customer_segment_name: str
    image_url: str
    terms_conditions: str
    notification_message: str
    settings_json: str


@dataclass(frozen=True)
class CampaignTypeView:
    id: str
    code: str
    name: str
    description: str
    icon: str
    is_active: bool
    display_order: int
    settings_json: str


@dataclass(frozen=True)
class CampaignRuleView:
    id: str
    campaign_id: str
    campaign_label: str
    rule_type: str
    rule_value: str
    fk_product_id: str | None
    product_label: str
    fk_department_id: str | None
    department_label: str
    fk_payment_type_id: str | None
    payment_type_label: str
    fk_product_manufacturer_id: str | None
    manufacturer_label: str
    is_include: bool
    description: str
    settings_json: str


@dataclass(frozen=True)
class CampaignProductView:
    id: str
    campaign_id: str
    campaign_label: str
    product_id: str
    product_label: str
    is_gift_product: bool
    min_quantity: int | None
    max_quantity: int | None
    discount_value: Decimal
    discount_percentage: Decimal
    is_active: bool
    display_order: int


@dataclass(frozen=True)
class CampaignUsageView:
    id: str
    campaign_id: str
    campaign_label: str
    customer_id: str | None
    customer_label: str
    transaction_id: str | None
    transaction_label: str
    store_id: str | None
    store_label: str
    cashier_id: str | None
    cashier_label: str
    discount_amount: Decimal
    usage_date: datetime | None
    coupon_code: str
    notes: str


@dataclass(frozen=True)
class CampaignOperationView:
    campaign_id: str
    campaign_code: str
    campaign_name: str
    campaign_type_name: str
    is_active: bool
    usage_count: int
    total_discount_amount: Decimal
    last_usage_at: datetime | None


class CampaignManagementService:
    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_campaigns(self, search_text: str | None = None) -> list[CampaignView]:
        with self._engine.get_session() as session:
            query = (
                session.query(Campaign, CampaignType, Store, CustomerSegment)
                .join(CampaignType, CampaignType.id == Campaign.fk_campaign_type_id)
                .outerjoin(Store, Store.id == Campaign.fk_store_id)
                .outerjoin(CustomerSegment, CustomerSegment.id == Campaign.fk_customer_segment_id)
                .filter(Campaign.is_deleted.is_(False), CampaignType.is_deleted.is_(False))
                .order_by(asc(Campaign.code))
            )
            search_value = (search_text or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(
                    Campaign.code.ilike(pattern)
                    | Campaign.name.ilike(pattern)
                    | Campaign.description.ilike(pattern)
                )
            rows = query.all()
            return [
                CampaignView(
                    id=str(campaign.id),
                    code=campaign.code,
                    name=campaign.name,
                    description=campaign.description or "",
                    fk_campaign_type_id=str(campaign.fk_campaign_type_id),
                    campaign_type_name=campaign_type.name,
                    fk_store_id=str(campaign.fk_store_id) if campaign.fk_store_id else None,
                    store_label=store.store_code if store else "All Stores",
                    discount_type=campaign.discount_type or "",
                    discount_value=Decimal(str(campaign.discount_value or 0)),
                    discount_percentage=Decimal(str(campaign.discount_percentage or 0)),
                    max_discount_amount=Decimal(str(campaign.max_discount_amount or 0)),
                    min_purchase_amount=Decimal(str(campaign.min_purchase_amount or 0)),
                    max_purchase_amount=Decimal(str(campaign.max_purchase_amount or 0)),
                    buy_quantity=int(campaign.buy_quantity or 0),
                    get_quantity=int(campaign.get_quantity or 0),
                    start_date=campaign.start_date,
                    end_date=campaign.end_date,
                    start_time=campaign.start_time,
                    end_time=campaign.end_time,
                    days_of_week=campaign.days_of_week or "",
                    priority=int(campaign.priority or 1),
                    is_combinable=bool(campaign.is_combinable),
                    usage_limit_per_customer=campaign.usage_limit_per_customer,
                    total_usage_limit=campaign.total_usage_limit,
                    total_usage_count=int(campaign.total_usage_count or 0),
                    is_active=bool(campaign.is_active),
                    is_auto_apply=bool(campaign.is_auto_apply),
                    requires_coupon=bool(campaign.requires_coupon),
                    fk_customer_segment_id=(
                        str(campaign.fk_customer_segment_id)
                        if campaign.fk_customer_segment_id
                        else None
                    ),
                    customer_segment_name=customer_segment.name if customer_segment else "All Customers",
                    image_url=campaign.image_url or "",
                    terms_conditions=campaign.terms_conditions or "",
                    notification_message=campaign.notification_message or "",
                    settings_json=campaign.settings_json or "",
                )
                for campaign, campaign_type, store, customer_segment in rows
            ]

    def save_campaign(self, payload: dict[str, Any], campaign_id: str | None = None) -> ServiceResult:
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        campaign_type_id = str(payload.get("fk_campaign_type_id", "")).strip()
        if not code or not name or not campaign_type_id:
            return ServiceResult(False, "Campaign code, name, and campaign type are required.")

        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(Campaign)
                    .filter(Campaign.code == code, Campaign.is_deleted.is_(False))
                    .first()
                )
                if existing and str(existing.id) != str(campaign_id):
                    return ServiceResult(False, f"Campaign code '{code}' is already in use.")

                if campaign_id:
                    campaign = (
                        session.query(Campaign)
                        .filter(Campaign.id == self._as_uuid(campaign_id), Campaign.is_deleted.is_(False))
                        .first()
                    )
                    if campaign is None:
                        return ServiceResult(False, "Campaign record not found.")
                else:
                    campaign = Campaign()
                    session.add(campaign)

                campaign.code = code
                campaign.name = name
                campaign.description = str(payload.get("description", "")).strip() or None
                campaign.fk_campaign_type_id = self._as_uuid(campaign_type_id)
                campaign.fk_store_id = self._as_uuid(payload.get("fk_store_id")) or self._as_uuid(
                    self._resolve_store_id()
                )
                campaign.discount_type = str(payload.get("discount_type", "")).strip() or None
                campaign.discount_value = Decimal(str(payload.get("discount_value", 0)))
                campaign.discount_percentage = Decimal(str(payload.get("discount_percentage", 0)))
                campaign.max_discount_amount = Decimal(str(payload.get("max_discount_amount", 0)))
                campaign.min_purchase_amount = Decimal(str(payload.get("min_purchase_amount", 0)))
                campaign.max_purchase_amount = Decimal(str(payload.get("max_purchase_amount", 0)))
                campaign.buy_quantity = int(payload.get("buy_quantity", 0)) or None
                campaign.get_quantity = int(payload.get("get_quantity", 0)) or None
                campaign.start_date = payload.get("start_date")
                campaign.end_date = payload.get("end_date")
                campaign.start_time = payload.get("start_time")
                campaign.end_time = payload.get("end_time")
                campaign.days_of_week = str(payload.get("days_of_week", "")).strip() or None
                campaign.priority = int(payload.get("priority", 1))
                campaign.is_combinable = bool(payload.get("is_combinable", False))
                campaign.usage_limit_per_customer = (
                    int(payload["usage_limit_per_customer"])
                    if payload.get("usage_limit_per_customer") not in (None, "")
                    else None
                )
                campaign.total_usage_limit = (
                    int(payload["total_usage_limit"])
                    if payload.get("total_usage_limit") not in (None, "")
                    else None
                )
                campaign.total_usage_count = int(payload.get("total_usage_count", 0))
                campaign.is_active = bool(payload.get("is_active", True))
                campaign.is_auto_apply = bool(payload.get("is_auto_apply", False))
                campaign.requires_coupon = bool(payload.get("requires_coupon", False))
                campaign.fk_customer_segment_id = self._as_uuid(payload.get("fk_customer_segment_id"))
                campaign.image_url = str(payload.get("image_url", "")).strip() or None
                campaign.terms_conditions = str(payload.get("terms_conditions", "")).strip() or None
                campaign.notification_message = (
                    str(payload.get("notification_message", "")).strip() or None
                )
                campaign.settings_json = str(payload.get("settings_json", "")).strip() or None

                return ServiceResult(
                    True,
                    "Campaign updated successfully."
                    if campaign_id
                    else "Campaign created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(False, "Campaign save operation failed due to a database error.")

    def delete_campaign(self, campaign_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                campaign = (
                    session.query(Campaign)
                    .filter(Campaign.id == self._as_uuid(campaign_id), Campaign.is_deleted.is_(False))
                    .first()
                )
                if campaign is None:
                    return ServiceResult(False, "Campaign record not found.")
                campaign.is_deleted = True
                return ServiceResult(True, "Campaign deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Campaign delete operation failed due to a database error.")

    def list_campaign_types(self) -> list[CampaignTypeView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(CampaignType)
                .filter(CampaignType.is_deleted.is_(False))
                .order_by(asc(CampaignType.display_order), asc(CampaignType.code))
                .all()
            )
            return [
                CampaignTypeView(
                    id=str(row.id),
                    code=row.code,
                    name=row.name,
                    description=row.description or "",
                    icon=row.icon or "",
                    is_active=bool(row.is_active),
                    display_order=int(row.display_order or 0),
                    settings_json=row.settings_json or "",
                )
                for row in rows
            ]

    def save_campaign_type(
        self,
        payload: dict[str, Any],
        campaign_type_id: str | None = None,
    ) -> ServiceResult:
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        if not code or not name:
            return ServiceResult(False, "Campaign type code and name are required.")

        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(CampaignType)
                    .filter(CampaignType.code == code, CampaignType.is_deleted.is_(False))
                    .first()
                )
                if existing and str(existing.id) != str(campaign_type_id):
                    return ServiceResult(False, f"Campaign type code '{code}' is already in use.")

                if campaign_type_id:
                    campaign_type = (
                        session.query(CampaignType)
                        .filter(
                            CampaignType.id == self._as_uuid(campaign_type_id),
                            CampaignType.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if campaign_type is None:
                        return ServiceResult(False, "Campaign type record not found.")
                else:
                    campaign_type = CampaignType()
                    session.add(campaign_type)

                campaign_type.code = code
                campaign_type.name = name
                campaign_type.description = str(payload.get("description", "")).strip() or None
                campaign_type.icon = str(payload.get("icon", "")).strip() or None
                campaign_type.is_active = bool(payload.get("is_active", True))
                campaign_type.display_order = int(payload.get("display_order", 0))
                campaign_type.settings_json = str(payload.get("settings_json", "")).strip() or None

                return ServiceResult(
                    True,
                    "Campaign type updated successfully."
                    if campaign_type_id
                    else "Campaign type created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Campaign type save operation failed due to a database error.")

    def delete_campaign_type(self, campaign_type_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                campaign_type = (
                    session.query(CampaignType)
                    .filter(
                        CampaignType.id == self._as_uuid(campaign_type_id),
                        CampaignType.is_deleted.is_(False),
                    )
                    .first()
                )
                if campaign_type is None:
                    return ServiceResult(False, "Campaign type record not found.")
                campaign_type.is_deleted = True
                return ServiceResult(True, "Campaign type deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Campaign type delete operation failed due to a database error.")

    def list_campaign_rules(self, campaign_id: str | None = None) -> list[CampaignRuleView]:
        with self._engine.get_session() as session:
            query = (
                session.query(
                    CampaignRule,
                    Campaign,
                    Product,
                    DepartmentMainGroup,
                    PaymentType,
                    ProductManufacturer,
                )
                .join(Campaign, Campaign.id == CampaignRule.fk_campaign_id)
                .outerjoin(Product, Product.id == CampaignRule.fk_product_id)
                .outerjoin(DepartmentMainGroup, DepartmentMainGroup.id == CampaignRule.fk_department_id)
                .outerjoin(PaymentType, PaymentType.id == CampaignRule.fk_payment_type_id)
                .outerjoin(
                    ProductManufacturer,
                    ProductManufacturer.id == CampaignRule.fk_product_manufacturer_id,
                )
                .filter(CampaignRule.is_deleted.is_(False), Campaign.is_deleted.is_(False))
                .order_by(asc(Campaign.code), asc(CampaignRule.rule_type))
            )
            if campaign_id:
                query = query.filter(CampaignRule.fk_campaign_id == self._as_uuid(campaign_id))
            rows = query.all()
            return [
                CampaignRuleView(
                    id=str(rule.id),
                    campaign_id=str(campaign.id),
                    campaign_label=f"{campaign.code} - {campaign.name}",
                    rule_type=rule.rule_type,
                    rule_value=rule.rule_value or "",
                    fk_product_id=str(rule.fk_product_id) if rule.fk_product_id else None,
                    product_label=f"{product.code} - {product.name}" if product else "-",
                    fk_department_id=str(rule.fk_department_id) if rule.fk_department_id else None,
                    department_label=f"{department.code} - {department.name}" if department else "-",
                    fk_payment_type_id=(
                        str(rule.fk_payment_type_id) if rule.fk_payment_type_id else None
                    ),
                    payment_type_label=f"{payment_type.type_no} - {payment_type.type_name}"
                    if payment_type
                    else "-",
                    fk_product_manufacturer_id=(
                        str(rule.fk_product_manufacturer_id)
                        if rule.fk_product_manufacturer_id
                        else None
                    ),
                    manufacturer_label=manufacturer.name if manufacturer else "-",
                    is_include=bool(rule.is_include),
                    description=rule.description or "",
                    settings_json=rule.settings_json or "",
                )
                for rule, campaign, product, department, payment_type, manufacturer in rows
            ]

    def save_campaign_rule(
        self,
        payload: dict[str, Any],
        rule_id: str | None = None,
    ) -> ServiceResult:
        campaign_id = str(payload.get("campaign_id", "")).strip()
        rule_type = str(payload.get("rule_type", "")).strip()
        if not campaign_id or not rule_type:
            return ServiceResult(False, "Campaign and rule type are required.")

        try:
            with self._engine.get_session() as session:
                if rule_id:
                    rule = (
                        session.query(CampaignRule)
                        .filter(CampaignRule.id == self._as_uuid(rule_id), CampaignRule.is_deleted.is_(False))
                        .first()
                    )
                    if rule is None:
                        return ServiceResult(False, "Campaign rule record not found.")
                else:
                    rule = CampaignRule()
                    session.add(rule)

                rule.fk_campaign_id = self._as_uuid(campaign_id)
                rule.rule_type = rule_type
                rule.rule_value = str(payload.get("rule_value", "")).strip() or None
                rule.fk_product_id = self._as_uuid(payload.get("fk_product_id"))
                rule.fk_department_id = self._as_uuid(payload.get("fk_department_id"))
                rule.fk_payment_type_id = self._as_uuid(payload.get("fk_payment_type_id"))
                rule.fk_product_manufacturer_id = self._as_uuid(
                    payload.get("fk_product_manufacturer_id")
                )
                rule.is_include = bool(payload.get("is_include", True))
                rule.description = str(payload.get("description", "")).strip() or None
                rule.settings_json = str(payload.get("settings_json", "")).strip() or None

                return ServiceResult(
                    True,
                    "Campaign rule updated successfully."
                    if rule_id
                    else "Campaign rule created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Campaign rule save operation failed due to a database error.")

    def delete_campaign_rule(self, rule_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                rule = (
                    session.query(CampaignRule)
                    .filter(CampaignRule.id == self._as_uuid(rule_id), CampaignRule.is_deleted.is_(False))
                    .first()
                )
                if rule is None:
                    return ServiceResult(False, "Campaign rule record not found.")
                rule.is_deleted = True
                return ServiceResult(True, "Campaign rule deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Campaign rule delete operation failed due to a database error.")

    def list_campaign_products(self, campaign_id: str | None = None) -> list[CampaignProductView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CampaignProduct, Campaign, Product)
                .join(Campaign, Campaign.id == CampaignProduct.fk_campaign_id)
                .join(Product, Product.id == CampaignProduct.fk_product_id)
                .filter(
                    CampaignProduct.is_deleted.is_(False),
                    Campaign.is_deleted.is_(False),
                    Product.is_deleted.is_(False),
                )
                .order_by(asc(Campaign.code), asc(Product.code))
            )
            if campaign_id:
                query = query.filter(CampaignProduct.fk_campaign_id == self._as_uuid(campaign_id))
            rows = query.all()
            return [
                CampaignProductView(
                    id=str(row.id),
                    campaign_id=str(campaign.id),
                    campaign_label=f"{campaign.code} - {campaign.name}",
                    product_id=str(product.id),
                    product_label=f"{product.code} - {product.name}",
                    is_gift_product=bool(row.is_gift_product),
                    min_quantity=row.min_quantity,
                    max_quantity=row.max_quantity,
                    discount_value=Decimal(str(row.discount_value or 0)),
                    discount_percentage=Decimal(str(row.discount_percentage or 0)),
                    is_active=bool(row.is_active),
                    display_order=int(row.display_order or 0),
                )
                for row, campaign, product in rows
            ]

    def save_campaign_product(
        self,
        payload: dict[str, Any],
        campaign_product_id: str | None = None,
    ) -> ServiceResult:
        campaign_id = str(payload.get("campaign_id", "")).strip()
        product_id = str(payload.get("product_id", "")).strip()
        if not campaign_id or not product_id:
            return ServiceResult(False, "Campaign and product are required.")

        try:
            with self._engine.get_session() as session:
                duplicate = (
                    session.query(CampaignProduct)
                    .filter(
                        CampaignProduct.fk_campaign_id == self._as_uuid(campaign_id),
                        CampaignProduct.fk_product_id == self._as_uuid(product_id),
                        CampaignProduct.is_deleted.is_(False),
                    )
                    .first()
                )
                if duplicate and str(duplicate.id) != str(campaign_product_id):
                    return ServiceResult(False, "Product already exists in this campaign.")

                if campaign_product_id:
                    campaign_product = (
                        session.query(CampaignProduct)
                        .filter(
                            CampaignProduct.id == self._as_uuid(campaign_product_id),
                            CampaignProduct.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if campaign_product is None:
                        return ServiceResult(False, "Campaign product record not found.")
                else:
                    campaign_product = CampaignProduct()
                    session.add(campaign_product)

                campaign_product.fk_campaign_id = self._as_uuid(campaign_id)
                campaign_product.fk_product_id = self._as_uuid(product_id)
                campaign_product.is_gift_product = bool(payload.get("is_gift_product", False))
                campaign_product.min_quantity = (
                    int(payload["min_quantity"])
                    if payload.get("min_quantity") not in (None, "")
                    else None
                )
                campaign_product.max_quantity = (
                    int(payload["max_quantity"])
                    if payload.get("max_quantity") not in (None, "")
                    else None
                )
                campaign_product.discount_value = Decimal(str(payload.get("discount_value", 0)))
                campaign_product.discount_percentage = Decimal(
                    str(payload.get("discount_percentage", 0))
                )
                campaign_product.is_active = bool(payload.get("is_active", True))
                campaign_product.display_order = int(payload.get("display_order", 0))

                return ServiceResult(
                    True,
                    "Campaign product updated successfully."
                    if campaign_product_id
                    else "Campaign product created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(
                False,
                "Campaign product save operation failed due to a database error.",
            )

    def delete_campaign_product(self, campaign_product_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                campaign_product = (
                    session.query(CampaignProduct)
                    .filter(
                        CampaignProduct.id == self._as_uuid(campaign_product_id),
                        CampaignProduct.is_deleted.is_(False),
                    )
                    .first()
                )
                if campaign_product is None:
                    return ServiceResult(False, "Campaign product record not found.")
                campaign_product.is_deleted = True
                return ServiceResult(True, "Campaign product deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Campaign product delete operation failed due to a database error.",
            )

    def list_campaign_usages(self, campaign_id: str | None = None) -> list[CampaignUsageView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CampaignUsage, Campaign, Customer, TransactionHead, Store, Cashier)
                .join(Campaign, Campaign.id == CampaignUsage.fk_campaign_id)
                .outerjoin(Customer, Customer.id == CampaignUsage.fk_customer_id)
                .outerjoin(TransactionHead, TransactionHead.id == CampaignUsage.fk_transaction_head_id)
                .outerjoin(Store, Store.id == CampaignUsage.fk_store_id)
                .outerjoin(Cashier, Cashier.id == CampaignUsage.fk_cashier_id)
                .filter(CampaignUsage.is_deleted.is_(False), Campaign.is_deleted.is_(False))
                .order_by(desc(CampaignUsage.usage_date))
            )
            if campaign_id:
                query = query.filter(CampaignUsage.fk_campaign_id == self._as_uuid(campaign_id))
            rows = query.all()
            return [
                CampaignUsageView(
                    id=str(usage.id),
                    campaign_id=str(campaign.id),
                    campaign_label=f"{campaign.code} - {campaign.name}",
                    customer_id=str(customer.id) if customer else None,
                    customer_label=f"{customer.name} {customer.last_name}".strip()
                    if customer
                    else "-",
                    transaction_id=str(transaction.id) if transaction else None,
                    transaction_label=transaction.transaction_unique_id if transaction else "-",
                    store_id=str(store.id) if store else None,
                    store_label=store.store_code if store else "-",
                    cashier_id=str(cashier.id) if cashier else None,
                    cashier_label=f"{cashier.no} - {cashier.user_name}" if cashier else "-",
                    discount_amount=Decimal(str(usage.discount_amount or 0)),
                    usage_date=usage.usage_date,
                    coupon_code=usage.coupon_code or "",
                    notes=usage.notes or "",
                )
                for usage, campaign, customer, transaction, store, cashier in rows
            ]

    def save_campaign_usage(
        self,
        payload: dict[str, Any],
        usage_id: str | None = None,
    ) -> ServiceResult:
        campaign_id = str(payload.get("campaign_id", "")).strip()
        discount_amount = payload.get("discount_amount")
        if not campaign_id or discount_amount in (None, ""):
            return ServiceResult(False, "Campaign and discount amount are required.")

        try:
            with self._engine.get_session() as session:
                if usage_id:
                    usage = (
                        session.query(CampaignUsage)
                        .filter(CampaignUsage.id == self._as_uuid(usage_id), CampaignUsage.is_deleted.is_(False))
                        .first()
                    )
                    if usage is None:
                        return ServiceResult(False, "Campaign usage record not found.")
                else:
                    usage = CampaignUsage()
                    session.add(usage)

                usage.fk_campaign_id = self._as_uuid(campaign_id)
                usage.fk_customer_id = self._as_uuid(payload.get("fk_customer_id"))
                usage.fk_transaction_head_id = self._as_uuid(payload.get("fk_transaction_head_id"))
                usage.fk_store_id = self._as_uuid(payload.get("fk_store_id")) or self._as_uuid(
                    self._resolve_store_id()
                )
                usage.fk_cashier_id = self._as_uuid(payload.get("fk_cashier_id"))
                usage.discount_amount = Decimal(str(discount_amount))
                usage.usage_date = payload.get("usage_date") or datetime.now()
                usage.coupon_code = str(payload.get("coupon_code", "")).strip() or None
                usage.notes = str(payload.get("notes", "")).strip() or None

                return ServiceResult(
                    True,
                    "Campaign usage updated successfully."
                    if usage_id
                    else "Campaign usage created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(
                False,
                "Campaign usage save operation failed due to a database error.",
            )

    def delete_campaign_usage(self, usage_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                usage = (
                    session.query(CampaignUsage)
                    .filter(CampaignUsage.id == self._as_uuid(usage_id), CampaignUsage.is_deleted.is_(False))
                    .first()
                )
                if usage is None:
                    return ServiceResult(False, "Campaign usage record not found.")
                usage.is_deleted = True
                return ServiceResult(True, "Campaign usage deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Campaign usage delete operation failed due to a database error.",
            )

    def list_campaign_operations(self, campaign_id: str | None = None) -> list[CampaignOperationView]:
        with self._engine.get_session() as session:
            query = (
                session.query(
                    Campaign,
                    CampaignType,
                    func.count(CampaignUsage.id).label("usage_count"),
                    func.coalesce(func.sum(CampaignUsage.discount_amount), 0).label(
                        "total_discount_amount"
                    ),
                    func.max(CampaignUsage.usage_date).label("last_usage_at"),
                )
                .join(CampaignType, CampaignType.id == Campaign.fk_campaign_type_id)
                .outerjoin(
                    CampaignUsage,
                    (CampaignUsage.fk_campaign_id == Campaign.id)
                    & CampaignUsage.is_deleted.is_(False),
                )
                .filter(Campaign.is_deleted.is_(False), CampaignType.is_deleted.is_(False))
                .group_by(Campaign.id, CampaignType.id)
                .order_by(asc(Campaign.code))
            )
            if campaign_id:
                query = query.filter(Campaign.id == self._as_uuid(campaign_id))
            rows = query.all()
            return [
                CampaignOperationView(
                    campaign_id=str(campaign.id),
                    campaign_code=campaign.code,
                    campaign_name=campaign.name,
                    campaign_type_name=campaign_type.name,
                    is_active=bool(campaign.is_active),
                    usage_count=int(usage_count or 0),
                    total_discount_amount=Decimal(str(total_discount_amount or 0)),
                    last_usage_at=last_usage_at,
                )
                for campaign, campaign_type, usage_count, total_discount_amount, last_usage_at in rows
            ]

    def list_campaign_type_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=f"{row.code} - {row.name}")
            for row in self.list_campaign_types()
        ]

    def list_campaign_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=f"{row.code} - {row.name}")
            for row in self.list_campaigns()
        ]

    def list_product_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Product)
                .filter(Product.is_deleted.is_(False))
                .order_by(asc(Product.code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.code} - {row.name}")
                for row in rows
            ]

    def list_department_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(DepartmentMainGroup)
                .filter(DepartmentMainGroup.is_deleted.is_(False))
                .order_by(asc(DepartmentMainGroup.code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.code} - {row.name}")
                for row in rows
            ]

    def list_payment_type_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(PaymentType)
                .filter(PaymentType.is_deleted.is_(False))
                .order_by(asc(PaymentType.type_no))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.type_no} - {row.type_name}")
                for row in rows
            ]

    def list_manufacturer_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(ProductManufacturer)
                .filter(ProductManufacturer.is_deleted.is_(False))
                .order_by(asc(ProductManufacturer.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.name) for row in rows]

    def list_customer_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Customer)
                .filter(Customer.is_deleted.is_(False))
                .order_by(asc(Customer.name), asc(Customer.last_name))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.name} {row.last_name}".strip())
                for row in rows
            ]

    def list_cashier_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Cashier)
                .filter(Cashier.is_deleted.is_(False))
                .order_by(asc(Cashier.no))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.no} - {row.user_name}")
                for row in rows
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

    def list_customer_segment_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(CustomerSegment)
                .filter(CustomerSegment.is_deleted.is_(False))
                .order_by(asc(CustomerSegment.display_order), asc(CustomerSegment.code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.code} - {row.name}")
                for row in rows
            ]

    def _resolve_store_id(self) -> str | None:
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
