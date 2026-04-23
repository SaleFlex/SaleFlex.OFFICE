"""
Service layer for loyalty definition and operation workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc, case, desc, func
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.campaign import Campaign
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.coupon import Coupon
from data_layer.model.definition.coupon_usage import CouponUsage
from data_layer.model.definition.customer import Customer
from data_layer.model.definition.customer_loyalty import CustomerLoyalty
from data_layer.model.definition.loyalty_earn_rule import LoyaltyEarnRule
from data_layer.model.definition.loyalty_point_transaction import LoyaltyPointTransaction
from data_layer.model.definition.loyalty_program import LoyaltyProgram
from data_layer.model.definition.loyalty_program_policy import LoyaltyProgramPolicy
from data_layer.model.definition.loyalty_redemption_policy import LoyaltyRedemptionPolicy
from data_layer.model.definition.loyalty_tier import LoyaltyTier
from data_layer.model.definition.store import Store
from office.service.customer_management_service import LookupItem, ServiceResult


@dataclass(frozen=True)
class LoyaltyProgramView:
    id: str
    name: str
    description: str
    store_id: str | None
    points_per_currency: Decimal
    currency_per_point: Decimal
    min_purchase_for_points: Decimal
    point_expiry_days: int
    is_active: bool
    start_date: datetime | None
    end_date: datetime | None
    welcome_points: int
    birthday_points: int
    terms_conditions: str
    settings_json: str


@dataclass(frozen=True)
class LoyaltyTierView:
    id: str
    loyalty_program_id: str
    loyalty_program_label: str
    name: str
    code: str
    description: str
    min_points_required: int
    min_annual_spending: Decimal
    tier_level: int
    points_multiplier: Decimal
    discount_percentage: Decimal
    special_benefits: str
    color_code: str
    icon: str
    is_active: bool
    display_order: int


@dataclass(frozen=True)
class LoyaltyEarnRuleView:
    id: str
    loyalty_program_id: str
    loyalty_program_label: str
    rule_code: str
    rule_type: str
    priority: int
    is_active: bool
    config_json: str
    description: str


@dataclass(frozen=True)
class LoyaltyProgramPolicyView:
    id: str
    loyalty_program_id: str
    loyalty_program_label: str
    customer_identifier_type: str
    require_customer_phone_for_enrollment: bool
    default_phone_country_calling_code: str
    void_loyalty_points_policy: str
    integration_provider: str
    integration_settings_json: str


@dataclass(frozen=True)
class LoyaltyRedemptionPolicyView:
    id: str
    loyalty_program_id: str
    loyalty_program_label: str
    max_basket_amount_share_from_points: Decimal
    minimum_points_to_redeem: int
    points_redemption_step: int
    allow_partial_redemption: bool


@dataclass(frozen=True)
class LoyaltyOperationView:
    customer_loyalty_id: str
    customer_label: str
    loyalty_program_name: str
    loyalty_tier_name: str
    loyalty_card_number: str
    available_points: int
    lifetime_points: int
    total_spent: Decimal
    transaction_count: int
    earned_points: int
    redeemed_points: int
    last_transaction_at: datetime | None
    is_active: bool


@dataclass(frozen=True)
class CouponView:
    id: str
    code: str
    name: str
    description: str
    campaign_id: str
    campaign_label: str
    coupon_type: str
    customer_id: str | None
    customer_label: str
    start_date: datetime | None
    end_date: datetime | None
    usage_limit: int | None
    usage_count: int
    is_active: bool
    is_sent: bool
    sent_date: datetime | None
    sent_method: str


@dataclass(frozen=True)
class CouponUsageView:
    id: str
    coupon_id: str
    coupon_code: str
    coupon_name: str
    customer_id: str | None
    customer_label: str
    discount_amount: Decimal
    usage_date: datetime | None
    notes: str
    store_label: str
    cashier_label: str


class LoyaltyManagementService:
    def __init__(self) -> None:
        self._engine = Engine()

    def list_loyalty_programs(self) -> list[LoyaltyProgramView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(LoyaltyProgram)
                .filter(LoyaltyProgram.is_deleted.is_(False))
                .order_by(desc(LoyaltyProgram.is_active), asc(LoyaltyProgram.name))
                .all()
            )
            return [
                LoyaltyProgramView(
                    id=str(row.id),
                    name=row.name or "",
                    description=row.description or "",
                    store_id=str(row.fk_store_id) if row.fk_store_id else None,
                    points_per_currency=Decimal(str(row.points_per_currency or 0)),
                    currency_per_point=Decimal(str(row.currency_per_point or 0)),
                    min_purchase_for_points=Decimal(str(row.min_purchase_for_points or 0)),
                    point_expiry_days=int(row.point_expiry_days or 0),
                    is_active=bool(row.is_active),
                    start_date=row.start_date,
                    end_date=row.end_date,
                    welcome_points=int(row.welcome_points or 0),
                    birthday_points=int(row.birthday_points or 0),
                    terms_conditions=row.terms_conditions or "",
                    settings_json=row.settings_json or "",
                )
                for row in rows
            ]

    def save_loyalty_program(
        self,
        payload: dict[str, Any],
        program_id: str | None = None,
    ) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        if not name:
            return ServiceResult(False, "Loyalty program name is required.")
        try:
            with self._engine.get_session() as session:
                existing_by_name = (
                    session.query(LoyaltyProgram)
                    .filter(LoyaltyProgram.name == name, LoyaltyProgram.is_deleted.is_(False))
                    .first()
                )
                if existing_by_name and str(existing_by_name.id) != str(program_id):
                    return ServiceResult(False, "Loyalty program name is already in use.")

                if program_id:
                    row = (
                        session.query(LoyaltyProgram)
                        .filter(LoyaltyProgram.id == self._as_uuid(program_id), LoyaltyProgram.is_deleted.is_(False))
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Loyalty program record not found.")
                else:
                    row = LoyaltyProgram()
                    session.add(row)

                row.name = name
                row.description = str(payload.get("description", "")).strip()
                row.fk_store_id = self._as_uuid(payload.get("store_id"))
                row.points_per_currency = Decimal(str(payload.get("points_per_currency", 0) or 0))
                row.currency_per_point = Decimal(str(payload.get("currency_per_point", 0) or 0))
                row.min_purchase_for_points = Decimal(
                    str(payload.get("min_purchase_for_points", 0) or 0)
                )
                row.point_expiry_days = int(payload.get("point_expiry_days", 0) or 0)
                row.is_active = bool(payload.get("is_active", True))
                row.start_date = self._parse_datetime(payload.get("start_date"))
                row.end_date = self._parse_datetime(payload.get("end_date"))
                row.welcome_points = int(payload.get("welcome_points", 0) or 0)
                row.birthday_points = int(payload.get("birthday_points", 0) or 0)
                row.terms_conditions = str(payload.get("terms_conditions", "")).strip()
                row.settings_json = str(payload.get("settings_json", "")).strip()

                return ServiceResult(
                    True,
                    "Loyalty program updated successfully."
                    if program_id
                    else "Loyalty program created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Loyalty program save operation failed due to a database error.")

    def delete_loyalty_program(self, program_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyProgram,
            record_id=program_id,
            not_found_message="Loyalty program record not found.",
            success_message="Loyalty program deleted successfully.",
            fail_message="Loyalty program delete operation failed due to a database error.",
        )

    def list_loyalty_tiers(self, program_id: str | None = None) -> list[LoyaltyTierView]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyTier, LoyaltyProgram)
                .join(LoyaltyProgram, LoyaltyProgram.id == LoyaltyTier.fk_loyalty_program_id)
                .filter(
                    LoyaltyTier.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                )
                .order_by(asc(LoyaltyTier.display_order), asc(LoyaltyTier.tier_level), asc(LoyaltyTier.name))
            )
            if program_id:
                query = query.filter(LoyaltyTier.fk_loyalty_program_id == self._as_uuid(program_id))
            rows = query.all()
            return [
                LoyaltyTierView(
                    id=str(tier.id),
                    loyalty_program_id=str(tier.fk_loyalty_program_id),
                    loyalty_program_label=program.name or "",
                    name=tier.name or "",
                    code=tier.code or "",
                    description=tier.description or "",
                    min_points_required=int(tier.min_points_required or 0),
                    min_annual_spending=Decimal(str(tier.min_annual_spending or 0)),
                    tier_level=int(tier.tier_level or 0),
                    points_multiplier=Decimal(str(tier.points_multiplier or 1)),
                    discount_percentage=Decimal(str(tier.discount_percentage or 0)),
                    special_benefits=tier.special_benefits or "",
                    color_code=tier.color_code or "",
                    icon=tier.icon or "",
                    is_active=bool(tier.is_active),
                    display_order=int(tier.display_order or 0),
                )
                for tier, program in rows
            ]

    def save_loyalty_tier(
        self,
        payload: dict[str, Any],
        tier_id: str | None = None,
    ) -> ServiceResult:
        program_id = str(payload.get("loyalty_program_id", "")).strip()
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        if not program_id or not code or not name:
            return ServiceResult(False, "Program, code, and name are required for loyalty tier.")
        try:
            with self._engine.get_session() as session:
                existing_by_code = (
                    session.query(LoyaltyTier)
                    .filter(
                        LoyaltyTier.fk_loyalty_program_id == self._as_uuid(program_id),
                        LoyaltyTier.code == code,
                        LoyaltyTier.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_code and str(existing_by_code.id) != str(tier_id):
                    return ServiceResult(False, "Tier code is already in use for this program.")

                if tier_id:
                    row = (
                        session.query(LoyaltyTier)
                        .filter(LoyaltyTier.id == self._as_uuid(tier_id), LoyaltyTier.is_deleted.is_(False))
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Loyalty tier record not found.")
                else:
                    row = LoyaltyTier()
                    session.add(row)

                row.fk_loyalty_program_id = self._as_uuid(program_id)
                row.name = name
                row.code = code
                row.description = str(payload.get("description", "")).strip()
                row.min_points_required = int(payload.get("min_points_required", 0) or 0)
                row.min_annual_spending = Decimal(str(payload.get("min_annual_spending", 0) or 0))
                row.tier_level = int(payload.get("tier_level", 1) or 1)
                row.points_multiplier = Decimal(str(payload.get("points_multiplier", 1) or 1))
                row.discount_percentage = Decimal(str(payload.get("discount_percentage", 0) or 0))
                row.special_benefits = str(payload.get("special_benefits", "")).strip()
                row.color_code = str(payload.get("color_code", "")).strip()
                row.icon = str(payload.get("icon", "")).strip()
                row.is_active = bool(payload.get("is_active", True))
                row.display_order = int(payload.get("display_order", 0) or 0)

                return ServiceResult(
                    True,
                    "Loyalty tier updated successfully."
                    if tier_id
                    else "Loyalty tier created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Loyalty tier save operation failed due to a database error.")

    def delete_loyalty_tier(self, tier_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyTier,
            record_id=tier_id,
            not_found_message="Loyalty tier record not found.",
            success_message="Loyalty tier deleted successfully.",
            fail_message="Loyalty tier delete operation failed due to a database error.",
        )

    def list_loyalty_earn_rules(self, program_id: str | None = None) -> list[LoyaltyEarnRuleView]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyEarnRule, LoyaltyProgram)
                .join(LoyaltyProgram, LoyaltyProgram.id == LoyaltyEarnRule.fk_loyalty_program_id)
                .filter(
                    LoyaltyEarnRule.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                )
                .order_by(asc(LoyaltyEarnRule.priority), asc(LoyaltyEarnRule.rule_code))
            )
            if program_id:
                query = query.filter(LoyaltyEarnRule.fk_loyalty_program_id == self._as_uuid(program_id))
            rows = query.all()
            return [
                LoyaltyEarnRuleView(
                    id=str(rule.id),
                    loyalty_program_id=str(rule.fk_loyalty_program_id),
                    loyalty_program_label=program.name or "",
                    rule_code=rule.rule_code or "",
                    rule_type=rule.rule_type or "",
                    priority=int(rule.priority or 0),
                    is_active=bool(rule.is_active),
                    config_json=rule.config_json or "",
                    description=rule.description or "",
                )
                for rule, program in rows
            ]

    def save_loyalty_earn_rule(
        self,
        payload: dict[str, Any],
        rule_id: str | None = None,
    ) -> ServiceResult:
        program_id = str(payload.get("loyalty_program_id", "")).strip()
        rule_code = str(payload.get("rule_code", "")).strip()
        rule_type = str(payload.get("rule_type", "")).strip()
        if not program_id or not rule_code or not rule_type:
            return ServiceResult(False, "Program, rule code, and rule type are required.")
        try:
            with self._engine.get_session() as session:
                existing_by_code = (
                    session.query(LoyaltyEarnRule)
                    .filter(
                        LoyaltyEarnRule.fk_loyalty_program_id == self._as_uuid(program_id),
                        LoyaltyEarnRule.rule_code == rule_code,
                        LoyaltyEarnRule.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_code and str(existing_by_code.id) != str(rule_id):
                    return ServiceResult(False, "Rule code is already in use for this program.")

                if rule_id:
                    row = (
                        session.query(LoyaltyEarnRule)
                        .filter(
                            LoyaltyEarnRule.id == self._as_uuid(rule_id),
                            LoyaltyEarnRule.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Loyalty earn rule record not found.")
                else:
                    row = LoyaltyEarnRule()
                    session.add(row)

                row.fk_loyalty_program_id = self._as_uuid(program_id)
                row.rule_code = rule_code
                row.rule_type = rule_type
                row.priority = int(payload.get("priority", 100) or 100)
                row.is_active = bool(payload.get("is_active", True))
                row.config_json = str(payload.get("config_json", "")).strip()
                row.description = str(payload.get("description", "")).strip()

                return ServiceResult(
                    True,
                    "Loyalty earn rule updated successfully."
                    if rule_id
                    else "Loyalty earn rule created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Loyalty earn rule save operation failed due to a database error.")

    def delete_loyalty_earn_rule(self, rule_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyEarnRule,
            record_id=rule_id,
            not_found_message="Loyalty earn rule record not found.",
            success_message="Loyalty earn rule deleted successfully.",
            fail_message="Loyalty earn rule delete operation failed due to a database error.",
        )

    def list_loyalty_program_policies(
        self,
        program_id: str | None = None,
    ) -> list[LoyaltyProgramPolicyView]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyProgramPolicy, LoyaltyProgram)
                .join(LoyaltyProgram, LoyaltyProgram.id == LoyaltyProgramPolicy.fk_loyalty_program_id)
                .filter(
                    LoyaltyProgramPolicy.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                )
                .order_by(asc(LoyaltyProgram.name))
            )
            if program_id:
                query = query.filter(LoyaltyProgramPolicy.fk_loyalty_program_id == self._as_uuid(program_id))
            rows = query.all()
            return [
                LoyaltyProgramPolicyView(
                    id=str(policy.id),
                    loyalty_program_id=str(policy.fk_loyalty_program_id),
                    loyalty_program_label=program.name or "",
                    customer_identifier_type=policy.customer_identifier_type or "",
                    require_customer_phone_for_enrollment=bool(
                        policy.require_customer_phone_for_enrollment
                    ),
                    default_phone_country_calling_code=policy.default_phone_country_calling_code or "",
                    void_loyalty_points_policy=policy.void_loyalty_points_policy or "",
                    integration_provider=policy.integration_provider or "",
                    integration_settings_json=policy.integration_settings_json or "",
                )
                for policy, program in rows
            ]

    def save_loyalty_program_policy(
        self,
        payload: dict[str, Any],
        policy_id: str | None = None,
    ) -> ServiceResult:
        program_id = str(payload.get("loyalty_program_id", "")).strip()
        if not program_id:
            return ServiceResult(False, "Program is required for policy.")
        try:
            with self._engine.get_session() as session:
                existing_by_program = (
                    session.query(LoyaltyProgramPolicy)
                    .filter(
                        LoyaltyProgramPolicy.fk_loyalty_program_id == self._as_uuid(program_id),
                        LoyaltyProgramPolicy.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_program and str(existing_by_program.id) != str(policy_id):
                    return ServiceResult(False, "There is already an active policy for this program.")

                if policy_id:
                    row = (
                        session.query(LoyaltyProgramPolicy)
                        .filter(
                            LoyaltyProgramPolicy.id == self._as_uuid(policy_id),
                            LoyaltyProgramPolicy.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Loyalty program policy record not found.")
                else:
                    row = LoyaltyProgramPolicy()
                    session.add(row)

                row.fk_loyalty_program_id = self._as_uuid(program_id)
                row.customer_identifier_type = str(
                    payload.get("customer_identifier_type", "PHONE")
                ).strip() or "PHONE"
                row.require_customer_phone_for_enrollment = bool(
                    payload.get("require_customer_phone_for_enrollment", True)
                )
                row.default_phone_country_calling_code = str(
                    payload.get("default_phone_country_calling_code", "")
                ).strip()
                row.void_loyalty_points_policy = str(
                    payload.get("void_loyalty_points_policy", "NONE")
                ).strip() or "NONE"
                row.integration_provider = str(payload.get("integration_provider", "LOCAL")).strip() or "LOCAL"
                row.integration_settings_json = str(
                    payload.get("integration_settings_json", "")
                ).strip()

                return ServiceResult(
                    True,
                    "Loyalty program policy updated successfully."
                    if policy_id
                    else "Loyalty program policy created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Loyalty program policy save operation failed due to a database error.")

    def delete_loyalty_program_policy(self, policy_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyProgramPolicy,
            record_id=policy_id,
            not_found_message="Loyalty program policy record not found.",
            success_message="Loyalty program policy deleted successfully.",
            fail_message="Loyalty program policy delete operation failed due to a database error.",
        )

    def list_loyalty_redemption_policies(
        self,
        program_id: str | None = None,
    ) -> list[LoyaltyRedemptionPolicyView]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyRedemptionPolicy, LoyaltyProgram)
                .join(LoyaltyProgram, LoyaltyProgram.id == LoyaltyRedemptionPolicy.fk_loyalty_program_id)
                .filter(
                    LoyaltyRedemptionPolicy.is_deleted.is_(False),
                    LoyaltyProgram.is_deleted.is_(False),
                )
                .order_by(asc(LoyaltyProgram.name))
            )
            if program_id:
                query = query.filter(
                    LoyaltyRedemptionPolicy.fk_loyalty_program_id == self._as_uuid(program_id)
                )
            rows = query.all()
            return [
                LoyaltyRedemptionPolicyView(
                    id=str(policy.id),
                    loyalty_program_id=str(policy.fk_loyalty_program_id),
                    loyalty_program_label=program.name or "",
                    max_basket_amount_share_from_points=Decimal(
                        str(policy.max_basket_amount_share_from_points or 0)
                    ),
                    minimum_points_to_redeem=int(policy.minimum_points_to_redeem or 0),
                    points_redemption_step=int(policy.points_redemption_step or 1),
                    allow_partial_redemption=bool(policy.allow_partial_redemption),
                )
                for policy, program in rows
            ]

    def save_loyalty_redemption_policy(
        self,
        payload: dict[str, Any],
        policy_id: str | None = None,
    ) -> ServiceResult:
        program_id = str(payload.get("loyalty_program_id", "")).strip()
        if not program_id:
            return ServiceResult(False, "Program is required for redemption policy.")
        try:
            with self._engine.get_session() as session:
                existing_by_program = (
                    session.query(LoyaltyRedemptionPolicy)
                    .filter(
                        LoyaltyRedemptionPolicy.fk_loyalty_program_id == self._as_uuid(program_id),
                        LoyaltyRedemptionPolicy.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_program and str(existing_by_program.id) != str(policy_id):
                    return ServiceResult(False, "There is already an active redemption policy for this program.")

                if policy_id:
                    row = (
                        session.query(LoyaltyRedemptionPolicy)
                        .filter(
                            LoyaltyRedemptionPolicy.id == self._as_uuid(policy_id),
                            LoyaltyRedemptionPolicy.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Loyalty redemption policy record not found.")
                else:
                    row = LoyaltyRedemptionPolicy()
                    session.add(row)

                row.fk_loyalty_program_id = self._as_uuid(program_id)
                max_share_raw = str(payload.get("max_basket_amount_share_from_points", "")).strip()
                row.max_basket_amount_share_from_points = (
                    Decimal(max_share_raw) if max_share_raw else None
                )
                row.minimum_points_to_redeem = int(payload.get("minimum_points_to_redeem", 0) or 0)
                row.points_redemption_step = int(payload.get("points_redemption_step", 1) or 1)
                row.allow_partial_redemption = bool(payload.get("allow_partial_redemption", True))

                return ServiceResult(
                    True,
                    "Loyalty redemption policy updated successfully."
                    if policy_id
                    else "Loyalty redemption policy created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Loyalty redemption policy save operation failed due to a database error.",
            )

    def delete_loyalty_redemption_policy(self, policy_id: str) -> ServiceResult:
        return self._soft_delete(
            model=LoyaltyRedemptionPolicy,
            record_id=policy_id,
            not_found_message="Loyalty redemption policy record not found.",
            success_message="Loyalty redemption policy deleted successfully.",
            fail_message="Loyalty redemption policy delete operation failed due to a database error.",
        )

    def list_loyalty_operations(
        self,
        program_id: str | None = None,
        customer_id: str | None = None,
        active_only: bool | None = None,
    ) -> list[LoyaltyOperationView]:
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
            if program_id:
                query = query.filter(CustomerLoyalty.fk_loyalty_program_id == self._as_uuid(program_id))
            if customer_id:
                query = query.filter(CustomerLoyalty.fk_customer_id == self._as_uuid(customer_id))
            if active_only is True:
                query = query.filter(CustomerLoyalty.is_active.is_(True))
            if active_only is False:
                query = query.filter(CustomerLoyalty.is_active.is_(False))
            rows = query.all()
            if not rows:
                return []

            loyalty_ids = [row.id for row, *_ in rows]
            txn_rows = (
                session.query(
                    LoyaltyPointTransaction.fk_customer_loyalty_id,
                    func.count(LoyaltyPointTransaction.id),
                    func.coalesce(func.sum(LoyaltyPointTransaction.points_amount), 0),
                    func.coalesce(
                        func.sum(
                            case(
                                (LoyaltyPointTransaction.points_amount > 0, LoyaltyPointTransaction.points_amount),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(
                            case(
                                (LoyaltyPointTransaction.points_amount < 0, -LoyaltyPointTransaction.points_amount),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    func.max(LoyaltyPointTransaction.transaction_date),
                )
                .filter(
                    LoyaltyPointTransaction.is_deleted.is_(False),
                    LoyaltyPointTransaction.fk_customer_loyalty_id.in_(loyalty_ids),
                )
                .group_by(LoyaltyPointTransaction.fk_customer_loyalty_id)
                .all()
            )
            txn_map = {
                loyalty_id: (
                    int(count or 0),
                    int(net_points or 0),
                    int(earned_points or 0),
                    int(redeemed_points or 0),
                    last_at,
                )
                for loyalty_id, count, net_points, earned_points, redeemed_points, last_at in txn_rows
            }

            return [
                LoyaltyOperationView(
                    customer_loyalty_id=str(loyalty.id),
                    customer_label=f"{customer.name} {customer.last_name}".strip(),
                    loyalty_program_name=program.name or "",
                    loyalty_tier_name=tier.name if tier else "",
                    loyalty_card_number=loyalty.loyalty_card_number or "",
                    available_points=int(loyalty.available_points or 0),
                    lifetime_points=int(loyalty.lifetime_points or 0),
                    total_spent=Decimal(str(loyalty.total_spent or 0)),
                    transaction_count=txn_map.get(loyalty.id, (0, 0, 0, 0, None))[0],
                    earned_points=txn_map.get(loyalty.id, (0, 0, 0, 0, None))[2],
                    redeemed_points=txn_map.get(loyalty.id, (0, 0, 0, 0, None))[3],
                    last_transaction_at=txn_map.get(loyalty.id, (0, 0, 0, 0, None))[4],
                    is_active=bool(loyalty.is_active),
                )
                for loyalty, customer, program, tier in rows
            ]

    def list_coupons(
        self,
        customer_id: str | None = None,
        campaign_id: str | None = None,
        active_only: bool | None = None,
    ) -> list[CouponView]:
        with self._engine.get_session() as session:
            query = (
                session.query(Coupon, Campaign, Customer)
                .join(Campaign, Campaign.id == Coupon.fk_campaign_id)
                .outerjoin(Customer, Customer.id == Coupon.fk_customer_id)
                .filter(
                    Coupon.is_deleted.is_(False),
                    Campaign.is_deleted.is_(False),
                )
                .order_by(asc(Coupon.code))
            )
            if customer_id:
                query = query.filter(Coupon.fk_customer_id == self._as_uuid(customer_id))
            if campaign_id:
                query = query.filter(Coupon.fk_campaign_id == self._as_uuid(campaign_id))
            if active_only is True:
                query = query.filter(Coupon.is_active.is_(True))
            if active_only is False:
                query = query.filter(Coupon.is_active.is_(False))
            rows = query.all()
            return [
                CouponView(
                    id=str(coupon.id),
                    code=coupon.code or "",
                    name=coupon.name or "",
                    description=coupon.description or "",
                    campaign_id=str(coupon.fk_campaign_id),
                    campaign_label=campaign.name or "",
                    coupon_type=coupon.coupon_type or "",
                    customer_id=str(coupon.fk_customer_id) if coupon.fk_customer_id else None,
                    customer_label=(
                        f"{customer.name} {customer.last_name}".strip()
                        if customer
                        else ""
                    ),
                    start_date=coupon.start_date,
                    end_date=coupon.end_date,
                    usage_limit=coupon.usage_limit,
                    usage_count=int(coupon.usage_count or 0),
                    is_active=bool(coupon.is_active),
                    is_sent=bool(coupon.is_sent),
                    sent_date=coupon.sent_date,
                    sent_method=coupon.sent_method or "",
                )
                for coupon, campaign, customer in rows
            ]

    def list_coupon_usages(
        self,
        customer_id: str | None = None,
        coupon_id: str | None = None,
    ) -> list[CouponUsageView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CouponUsage, Coupon, Customer, Store, Cashier)
                .join(Coupon, Coupon.id == CouponUsage.fk_coupon_id)
                .outerjoin(Customer, Customer.id == CouponUsage.fk_customer_id)
                .outerjoin(Store, Store.id == CouponUsage.fk_store_id)
                .outerjoin(Cashier, Cashier.id == CouponUsage.fk_cashier_id)
                .filter(CouponUsage.is_deleted.is_(False))
                .order_by(desc(CouponUsage.usage_date))
            )
            if customer_id:
                query = query.filter(CouponUsage.fk_customer_id == self._as_uuid(customer_id))
            if coupon_id:
                query = query.filter(CouponUsage.fk_coupon_id == self._as_uuid(coupon_id))
            rows = query.all()
            return [
                CouponUsageView(
                    id=str(usage.id),
                    coupon_id=str(usage.fk_coupon_id),
                    coupon_code=coupon.code or "",
                    coupon_name=coupon.name or "",
                    customer_id=str(usage.fk_customer_id) if usage.fk_customer_id else None,
                    customer_label=(
                        f"{customer.name} {customer.last_name}".strip()
                        if customer
                        else ""
                    ),
                    discount_amount=Decimal(str(usage.discount_amount or 0)),
                    usage_date=usage.usage_date,
                    notes=usage.notes or "",
                    store_label=(store.brand_name or store.store_code or "") if store else "",
                    cashier_label=(
                        f"{cashier.name} {cashier.last_name}".strip()
                        if cashier
                        else ""
                    ),
                )
                for usage, coupon, customer, store, cashier in rows
            ]

    def list_campaign_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Campaign)
                .filter(Campaign.is_deleted.is_(False))
                .order_by(asc(Campaign.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.name or "") for row in rows]

    def list_coupon_lookups(self, customer_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(Coupon)
                .filter(Coupon.is_deleted.is_(False))
                .order_by(asc(Coupon.code))
            )
            if customer_id:
                query = query.filter(Coupon.fk_customer_id == self._as_uuid(customer_id))
            rows = query.all()
            return [LookupItem(id=str(row.id), label=f"{row.code} - {row.name}") for row in rows]

    def list_loyalty_program_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(LoyaltyProgram)
                .filter(LoyaltyProgram.is_deleted.is_(False))
                .order_by(desc(LoyaltyProgram.is_active), asc(LoyaltyProgram.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.name or "") for row in rows]

    def list_loyalty_tier_lookups(self, program_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(LoyaltyTier)
                .filter(LoyaltyTier.is_deleted.is_(False))
                .order_by(asc(LoyaltyTier.display_order), asc(LoyaltyTier.tier_level), asc(LoyaltyTier.name))
            )
            if program_id:
                query = query.filter(LoyaltyTier.fk_loyalty_program_id == self._as_uuid(program_id))
            rows = query.all()
            return [
                LookupItem(id=str(row.id), label=f"L{int(row.tier_level or 0)} - {row.name}")
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
    def _parse_datetime(value: Any) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        if "T" in raw:
            return datetime.fromisoformat(raw)
        if len(raw) == 16:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return datetime.fromisoformat(raw)

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
