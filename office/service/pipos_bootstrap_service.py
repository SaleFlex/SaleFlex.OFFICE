"""Build bootstrap payloads for PyPOS terminals from Office-owned models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BootstrapTopic:
    """Definition topic and model name returned to PyPOS."""

    topic_name: str
    model_name: str


class PyPosBootstrapService:
    """Topic registry for definition pull flow from Office to PyPOS."""

    TOPICS: tuple[BootstrapTopic, ...] = (
        BootstrapTopic(topic_name="store", model_name="Store"),
        BootstrapTopic(topic_name="cashiers", model_name="Cashier"),
        BootstrapTopic(topic_name="vat", model_name="Vat"),
        BootstrapTopic(topic_name="payment_types", model_name="PaymentType"),
        BootstrapTopic(topic_name="department_main_groups", model_name="DepartmentMainGroup"),
        BootstrapTopic(topic_name="department_sub_groups", model_name="DepartmentSubGroup"),
        BootstrapTopic(topic_name="products", model_name="Product"),
        BootstrapTopic(topic_name="campaigns", model_name="Campaign"),
        BootstrapTopic(topic_name="campaign_products", model_name="CampaignProduct"),
        BootstrapTopic(topic_name="loyalty_programs", model_name="LoyaltyProgram"),
        BootstrapTopic(topic_name="loyalty_policies", model_name="LoyaltyProgramPolicy"),
    )

    def list_topics(self) -> tuple[BootstrapTopic, ...]:
        """Return bootstrap topics exposed to connected PyPOS terminals."""
        return self.TOPICS

