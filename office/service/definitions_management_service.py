"""
Service layer for definitions management module workflows.

Covers: Country, CountryRegion, City, District, Currency, CurrencyTable,
        PaymentType, and Vat definition tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.city import City
from data_layer.model.definition.country import Country
from data_layer.model.definition.country_region import CountryRegion
from data_layer.model.definition.currency import Currency
from data_layer.model.definition.currency_table import CurrencyTable
from data_layer.model.definition.district import District
from data_layer.model.definition.payment_type import PaymentType
from data_layer.model.definition.transaction_discount_type import TransactionDiscountType
from data_layer.model.definition.transaction_document_type import TransactionDocumentType
from data_layer.model.definition.vat import Vat


# ---------------------------------------------------------------------------
# Shared result wrapper
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServiceResult:
    """Simple operation result used by UI forms."""

    success: bool
    message: str


@dataclass(frozen=True)
class LookupItem:
    """Generic id+label pair for combo-box population."""

    id: str
    label: str


# ---------------------------------------------------------------------------
# Read models (view dataclasses)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CountryView:
    id: str
    name: str
    iso_alpha2: str
    iso_alpha3: str
    iso_numeric: int | None


@dataclass(frozen=True)
class CountryRegionView:
    id: str
    fk_country_id: str
    country_name: str
    iso_3166_2: str
    region_code: str
    name: str
    region_type: str
    has_special_requirements: bool
    display_order: str
    description: str


@dataclass(frozen=True)
class CityView:
    id: str
    name: str
    code: str
    short_name: str
    numeric_code: int | None
    fk_country_id: str
    country_name: str


@dataclass(frozen=True)
class DistrictView:
    id: str
    name: str
    code: str
    short_name: str
    numeric_code: int | None
    fk_city_id: str
    city_name: str


@dataclass(frozen=True)
class CurrencyView:
    id: str
    no: int
    name: str
    currency_code: int | None
    sign: str
    sign_direction: str
    currency_symbol: str
    decimal_places: int


@dataclass(frozen=True)
class CurrencyRateView:
    id: str
    fk_base_currency_id: str
    base_currency_name: str
    fk_target_currency_id: str
    target_currency_name: str
    rate: Decimal


@dataclass(frozen=True)
class PaymentTypeView:
    id: str
    type_no: int
    type_name: str
    type_description: str
    culture_info: str


@dataclass(frozen=True)
class VatView:
    id: str
    name: str
    no: int
    rate: Decimal
    description: str


@dataclass(frozen=True)
class TransactionDocumentTypeView:
    id: str
    no: int
    name: str
    display_name: str
    description: str


@dataclass(frozen=True)
class TransactionDiscountTypeView:
    id: str
    code: str
    name: str
    display_name: str
    description: str


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class DefinitionsManagementService:
    """Coordinate CRUD for all static definition tables."""

    def __init__(self) -> None:
        self._engine = Engine()

    # ------------------------------------------------------------------
    # Country
    # ------------------------------------------------------------------

    def list_countries(self) -> list[CountryView]:
        with self._engine.get_session() as session:
            rows = session.query(Country).order_by(asc(Country.name)).all()
            return [
                CountryView(
                    id=str(r.id),
                    name=r.name or "",
                    iso_alpha2=r.iso_alpha2 or "",
                    iso_alpha3=r.iso_alpha3 or "",
                    iso_numeric=r.iso_numeric,
                )
                for r in rows
            ]

    def list_country_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = session.query(Country).order_by(asc(Country.name)).all()
            return [LookupItem(id=str(r.id), label=f"{r.name} ({r.iso_alpha2})") for r in rows]

    def add_country(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = Country(
                    name=data.get("name", ""),
                    iso_alpha2=data.get("iso_alpha2", ""),
                    iso_alpha3=data.get("iso_alpha3") or None,
                    iso_numeric=int(data["iso_numeric"]) if data.get("iso_numeric") else None,
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Country added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_country(self, country_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Country).filter(Country.id == country_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Country not found.")
                record.name = data.get("name", record.name)
                record.iso_alpha2 = data.get("iso_alpha2", record.iso_alpha2)
                record.iso_alpha3 = data.get("iso_alpha3") or record.iso_alpha3
                record.iso_numeric = int(data["iso_numeric"]) if data.get("iso_numeric") else record.iso_numeric
                session.commit()
            return ServiceResult(success=True, message="Country updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_country(self, country_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Country).filter(Country.id == country_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Country not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="Country deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # CountryRegion
    # ------------------------------------------------------------------

    def list_country_regions(self, country_id: str | None = None) -> list[CountryRegionView]:
        with self._engine.get_session() as session:
            query = (
                session.query(CountryRegion, Country)
                .join(Country, CountryRegion.fk_country_id == Country.id)
            )
            if country_id:
                query = query.filter(CountryRegion.fk_country_id == country_id)
            query = query.order_by(asc(CountryRegion.name))
            return [
                CountryRegionView(
                    id=str(r.id),
                    fk_country_id=str(r.fk_country_id),
                    country_name=c.name or "",
                    iso_3166_2=r.iso_3166_2 or "",
                    region_code=r.region_code or "",
                    name=r.name or "",
                    region_type=r.region_type or "",
                    has_special_requirements=bool(r.has_special_requirements),
                    display_order=r.display_order or "",
                    description=r.description or "",
                )
                for r, c in query.all()
            ]

    def add_country_region(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = CountryRegion()
                record.fk_country_id = data.get("fk_country_id")
                record.iso_3166_2 = data.get("iso_3166_2") or None
                record.region_code = data.get("region_code", "")
                record.name = data.get("name", "")
                record.region_type = data.get("region_type") or None
                record.has_special_requirements = bool(data.get("has_special_requirements", False))
                record.display_order = data.get("display_order") or None
                record.description = data.get("description") or None
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Country region added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_country_region(self, region_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(CountryRegion).filter(CountryRegion.id == region_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Country region not found.")
                record.fk_country_id = data.get("fk_country_id", record.fk_country_id)
                record.iso_3166_2 = data.get("iso_3166_2") or record.iso_3166_2
                record.region_code = data.get("region_code", record.region_code)
                record.name = data.get("name", record.name)
                record.region_type = data.get("region_type") or record.region_type
                record.has_special_requirements = bool(data.get("has_special_requirements", record.has_special_requirements))
                record.display_order = data.get("display_order") or record.display_order
                record.description = data.get("description") or record.description
                session.commit()
            return ServiceResult(success=True, message="Country region updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_country_region(self, region_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(CountryRegion).filter(CountryRegion.id == region_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Country region not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="Country region deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # City
    # ------------------------------------------------------------------

    def list_cities(self, country_id: str | None = None) -> list[CityView]:
        with self._engine.get_session() as session:
            query = (
                session.query(City, Country)
                .join(Country, City.fk_country_id == Country.id)
            )
            if country_id:
                query = query.filter(City.fk_country_id == country_id)
            query = query.order_by(asc(City.name))
            return [
                CityView(
                    id=str(c.id),
                    name=c.name or "",
                    code=c.code or "",
                    short_name=c.short_name or "",
                    numeric_code=c.numeric_code,
                    fk_country_id=str(c.fk_country_id),
                    country_name=co.name or "",
                )
                for c, co in query.all()
            ]

    def list_city_lookups(self, country_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = session.query(City)
            if country_id:
                query = query.filter(City.fk_country_id == country_id)
            rows = query.order_by(asc(City.name)).all()
            return [LookupItem(id=str(r.id), label=f"{r.name} ({r.code})") for r in rows]

    def add_city(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = City(
                    name=data.get("name", ""),
                    code=data.get("code", ""),
                    short_name=data.get("short_name") or None,
                    numeric_code=int(data["numeric_code"]) if data.get("numeric_code") else None,
                    fk_country_id=data.get("fk_country_id"),
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="City added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_city(self, city_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(City).filter(City.id == city_id).first()
                if record is None:
                    return ServiceResult(success=False, message="City not found.")
                record.name = data.get("name", record.name)
                record.code = data.get("code", record.code)
                record.short_name = data.get("short_name") or record.short_name
                record.numeric_code = int(data["numeric_code"]) if data.get("numeric_code") else record.numeric_code
                record.fk_country_id = data.get("fk_country_id", record.fk_country_id)
                session.commit()
            return ServiceResult(success=True, message="City updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_city(self, city_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(City).filter(City.id == city_id).first()
                if record is None:
                    return ServiceResult(success=False, message="City not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="City deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # District
    # ------------------------------------------------------------------

    def list_districts(self, city_id: str | None = None) -> list[DistrictView]:
        with self._engine.get_session() as session:
            query = (
                session.query(District, City)
                .join(City, District.fk_city_id == City.id)
            )
            if city_id:
                query = query.filter(District.fk_city_id == city_id)
            query = query.order_by(asc(District.name))
            return [
                DistrictView(
                    id=str(d.id),
                    name=d.name or "",
                    code=d.code or "",
                    short_name=d.short_name or "",
                    numeric_code=d.numeric_code,
                    fk_city_id=str(d.fk_city_id),
                    city_name=c.name or "",
                )
                for d, c in query.all()
            ]

    def add_district(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = District(
                    name=data.get("name", ""),
                    code=data.get("code", ""),
                    short_name=data.get("short_name") or None,
                    numeric_code=int(data["numeric_code"]) if data.get("numeric_code") else None,
                    fk_city_id=data.get("fk_city_id"),
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="District added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_district(self, district_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(District).filter(District.id == district_id).first()
                if record is None:
                    return ServiceResult(success=False, message="District not found.")
                record.name = data.get("name", record.name)
                record.code = data.get("code", record.code)
                record.short_name = data.get("short_name") or record.short_name
                record.numeric_code = int(data["numeric_code"]) if data.get("numeric_code") else record.numeric_code
                record.fk_city_id = data.get("fk_city_id", record.fk_city_id)
                session.commit()
            return ServiceResult(success=True, message="District updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_district(self, district_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(District).filter(District.id == district_id).first()
                if record is None:
                    return ServiceResult(success=False, message="District not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="District deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------

    def list_currencies(self) -> list[CurrencyView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Currency)
                .filter(Currency.is_deleted.is_(False))
                .order_by(asc(Currency.no))
                .all()
            )
            return [
                CurrencyView(
                    id=str(r.id),
                    no=r.no,
                    name=r.name or "",
                    currency_code=r.currency_code,
                    sign=r.sign or "",
                    sign_direction=r.sign_direction or "",
                    currency_symbol=r.currency_symbol or "",
                    decimal_places=r.decimal_places if r.decimal_places is not None else 2,
                )
                for r in rows
            ]

    def list_currency_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Currency)
                .filter(Currency.is_deleted.is_(False))
                .order_by(asc(Currency.no))
                .all()
            )
            return [LookupItem(id=str(r.id), label=f"{r.name} ({r.sign})") for r in rows]

    def add_currency(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = Currency(
                    no=int(data.get("no", 0)),
                    name=data.get("name", ""),
                    currency_code=int(data["currency_code"]) if data.get("currency_code") else None,
                    sign=data.get("sign") or None,
                    sign_direction=data.get("sign_direction") or None,
                    currency_symbol=data.get("currency_symbol") or None,
                    decimal_places=int(data.get("decimal_places", 2)),
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Currency added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_currency(self, currency_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Currency).filter(Currency.id == currency_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Currency not found.")
                record.no = int(data.get("no", record.no))
                record.name = data.get("name", record.name)
                record.currency_code = int(data["currency_code"]) if data.get("currency_code") else record.currency_code
                record.sign = data.get("sign") or record.sign
                record.sign_direction = data.get("sign_direction") or record.sign_direction
                record.currency_symbol = data.get("currency_symbol") or record.currency_symbol
                record.decimal_places = int(data.get("decimal_places", record.decimal_places))
                session.commit()
            return ServiceResult(success=True, message="Currency updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def soft_delete_currency(self, currency_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Currency).filter(Currency.id == currency_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Currency not found.")
                record.is_deleted = True
                session.commit()
            return ServiceResult(success=True, message="Currency deactivated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # CurrencyTable (Exchange Rates)
    # ------------------------------------------------------------------

    def list_currency_rates(self) -> list[CurrencyRateView]:
        with self._engine.get_session() as session:
            BaseCurrency = Currency.__class__
            base_alias = session.query(Currency).subquery()
            rows = session.query(CurrencyTable).filter(
                CurrencyTable.is_deleted.is_(False)
            ).order_by(asc(CurrencyTable.fk_base_currency_id)).all()

            result = []
            for r in rows:
                base = session.query(Currency).filter(Currency.id == r.fk_base_currency_id).first()
                target = session.query(Currency).filter(Currency.id == r.fk_target_currency_id).first()
                result.append(
                    CurrencyRateView(
                        id=str(r.id),
                        fk_base_currency_id=str(r.fk_base_currency_id),
                        base_currency_name=base.name if base else "",
                        fk_target_currency_id=str(r.fk_target_currency_id),
                        target_currency_name=target.name if target else "",
                        rate=r.rate if r.rate is not None else Decimal("0"),
                    )
                )
            return result

    def add_currency_rate(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = CurrencyTable(
                    fk_base_currency_id=data.get("fk_base_currency_id"),
                    fk_target_currency_id=data.get("fk_target_currency_id"),
                    rate=Decimal(str(data.get("rate", "1"))),
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Currency rate added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_currency_rate(self, rate_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(CurrencyTable).filter(CurrencyTable.id == rate_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Currency rate not found.")
                record.fk_base_currency_id = data.get("fk_base_currency_id", record.fk_base_currency_id)
                record.fk_target_currency_id = data.get("fk_target_currency_id", record.fk_target_currency_id)
                record.rate = Decimal(str(data.get("rate", str(record.rate))))
                session.commit()
            return ServiceResult(success=True, message="Currency rate updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def soft_delete_currency_rate(self, rate_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(CurrencyTable).filter(CurrencyTable.id == rate_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Currency rate not found.")
                record.is_deleted = True
                session.commit()
            return ServiceResult(success=True, message="Currency rate deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # PaymentType
    # ------------------------------------------------------------------

    def list_payment_types(self) -> list[PaymentTypeView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(PaymentType)
                .filter(PaymentType.is_deleted.is_(False))
                .order_by(asc(PaymentType.type_no))
                .all()
            )
            return [
                PaymentTypeView(
                    id=str(r.id),
                    type_no=r.type_no,
                    type_name=r.type_name or "",
                    type_description=r.type_description or "",
                    culture_info=r.culture_info or "",
                )
                for r in rows
            ]

    def add_payment_type(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = PaymentType(
                    type_no=int(data.get("type_no", 0)),
                    type_name=data.get("type_name", ""),
                    type_description=data.get("type_description") or None,
                    culture_info=data.get("culture_info") or "en-GB",
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Payment type added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_payment_type(self, pt_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(PaymentType).filter(PaymentType.id == pt_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Payment type not found.")
                record.type_no = int(data.get("type_no", record.type_no))
                record.type_name = data.get("type_name", record.type_name)
                record.type_description = data.get("type_description") or record.type_description
                record.culture_info = data.get("culture_info") or record.culture_info
                session.commit()
            return ServiceResult(success=True, message="Payment type updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def soft_delete_payment_type(self, pt_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(PaymentType).filter(PaymentType.id == pt_id).first()
                if record is None:
                    return ServiceResult(success=False, message="Payment type not found.")
                record.is_deleted = True
                session.commit()
            return ServiceResult(success=True, message="Payment type deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # VAT
    # ------------------------------------------------------------------

    def list_vats(self) -> list[VatView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Vat)
                .filter(Vat.is_deleted.is_(False))
                .order_by(asc(Vat.no))
                .all()
            )
            return [
                VatView(
                    id=str(r.id),
                    name=r.name or "",
                    no=r.no,
                    rate=r.rate if r.rate is not None else Decimal("0"),
                    description=r.description or "",
                )
                for r in rows
            ]

    def add_vat(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = Vat(
                    name=data.get("name", ""),
                    no=int(data.get("no", 0)),
                    rate=Decimal(str(data.get("rate", "0"))),
                    description=data.get("description") or None,
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="VAT added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_vat(self, vat_id: str, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Vat).filter(Vat.id == vat_id).first()
                if record is None:
                    return ServiceResult(success=False, message="VAT not found.")
                record.name = data.get("name", record.name)
                record.no = int(data.get("no", record.no))
                record.rate = Decimal(str(data.get("rate", str(record.rate))))
                record.description = data.get("description") or record.description
                session.commit()
            return ServiceResult(success=True, message="VAT updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def soft_delete_vat(self, vat_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = session.query(Vat).filter(Vat.id == vat_id).first()
                if record is None:
                    return ServiceResult(success=False, message="VAT not found.")
                record.is_deleted = True
                session.commit()
            return ServiceResult(success=True, message="VAT deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # Transaction Document Types
    # ------------------------------------------------------------------

    def list_transaction_document_types(self) -> list[TransactionDocumentTypeView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionDocumentType)
                .order_by(asc(TransactionDocumentType.no))
                .all()
            )
            return [
                TransactionDocumentTypeView(
                    id=str(r.id),
                    no=r.no if r.no is not None else 0,
                    name=r.name or "",
                    display_name=r.display_name or "",
                    description=r.description or "",
                )
                for r in rows
            ]

    def add_transaction_document_type(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = TransactionDocumentType(
                    no=int(data.get("no", 0)),
                    name=data.get("name", ""),
                    display_name=data.get("display_name") or None,
                    description=data.get("description") or None,
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Transaction document type added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_transaction_document_type(
        self, doc_type_id: str, data: dict[str, Any]
    ) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = (
                    session.query(TransactionDocumentType)
                    .filter(TransactionDocumentType.id == doc_type_id)
                    .first()
                )
                if record is None:
                    return ServiceResult(success=False, message="Transaction document type not found.")
                record.no = int(data.get("no", record.no))
                record.name = data.get("name", record.name)
                record.display_name = data.get("display_name") or record.display_name
                record.description = data.get("description") or record.description
                session.commit()
            return ServiceResult(success=True, message="Transaction document type updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_transaction_document_type(self, doc_type_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = (
                    session.query(TransactionDocumentType)
                    .filter(TransactionDocumentType.id == doc_type_id)
                    .first()
                )
                if record is None:
                    return ServiceResult(success=False, message="Transaction document type not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="Transaction document type deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    # ------------------------------------------------------------------
    # Transaction Discount Types
    # ------------------------------------------------------------------

    def list_transaction_discount_types(self) -> list[TransactionDiscountTypeView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(TransactionDiscountType)
                .order_by(asc(TransactionDiscountType.name))
                .all()
            )
            return [
                TransactionDiscountTypeView(
                    id=str(r.id),
                    code=r.code or "",
                    name=r.name or "",
                    display_name=r.display_name or "",
                    description=r.description or "",
                )
                for r in rows
            ]

    def add_transaction_discount_type(self, data: dict[str, Any]) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = TransactionDiscountType(
                    code=data.get("code", ""),
                    name=data.get("name", ""),
                    display_name=data.get("display_name") or None,
                    description=data.get("description") or None,
                )
                session.add(record)
                session.commit()
            return ServiceResult(success=True, message="Transaction discount type added successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def update_transaction_discount_type(
        self, discount_type_id: str, data: dict[str, Any]
    ) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = (
                    session.query(TransactionDiscountType)
                    .filter(TransactionDiscountType.id == discount_type_id)
                    .first()
                )
                if record is None:
                    return ServiceResult(success=False, message="Transaction discount type not found.")
                record.code = data.get("code", record.code)
                record.name = data.get("name", record.name)
                record.display_name = data.get("display_name") or record.display_name
                record.description = data.get("description") or record.description
                session.commit()
            return ServiceResult(success=True, message="Transaction discount type updated successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))

    def delete_transaction_discount_type(self, discount_type_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                record = (
                    session.query(TransactionDiscountType)
                    .filter(TransactionDiscountType.id == discount_type_id)
                    .first()
                )
                if record is None:
                    return ServiceResult(success=False, message="Transaction discount type not found.")
                session.delete(record)
                session.commit()
            return ServiceResult(success=True, message="Transaction discount type deleted successfully.")
        except SQLAlchemyError as exc:
            return ServiceResult(success=False, message=str(exc))
