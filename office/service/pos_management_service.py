"""
Service layer for POS management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import asc, case, func
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.form import Form
from data_layer.model.definition.form_control import FormControl
from data_layer.model.definition.form_control_tab import FormControlTab
from data_layer.model.definition.pos_settings import PosSettings
from data_layer.model.definition.pos_terminal import PosTerminal
from data_layer.model.definition.pos_virtual_keyboard import PosVirtualKeyboard
from data_layer.model.definition.store import Store


@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str


@dataclass(frozen=True)
class LookupItem:
    id: str
    label: str


@dataclass(frozen=True)
class PosTerminalView:
    id: str
    terminal_code: str
    terminal_name: str
    terminal_serial_no: str
    host_name: str
    ip_address: str
    app_mode: str
    software_version: str
    is_active: bool
    is_online: bool
    is_allowed_pull: bool
    pull_interval_seconds: int


@dataclass(frozen=True)
class PosSettingsView:
    id: str
    fk_pos_terminal_id: str | None
    terminal_label: str
    pos_no_in_store: int
    name: str
    owner_national_id: str
    owner_tax_id: str
    mac_address: str
    backend_type: str
    backend_ip1: str
    backend_port1: int | None
    backend_ip2: str
    backend_port2: int | None
    force_to_work_online: bool
    plu_update_no: int


@dataclass(frozen=True)
class PosVirtualKeyboardView:
    id: str
    name: str
    is_active: bool
    keyboard_width: int
    keyboard_height: int
    x_position: int
    y_position: int
    font_family: str
    font_size: int
    button_width: int
    button_height: int
    button_background_color: str
    button_pressed_color: str
    control_button_width: int
    control_button_active_color: str


@dataclass(frozen=True)
class FormView:
    id: str
    form_no: int
    name: str
    function: str
    caption: str
    width: int | None
    height: int | None
    display_mode: str
    need_login: bool
    need_auth: bool
    use_virtual_keyboard: bool
    is_visible: bool
    is_startup: bool
    is_shared_across_pos: bool
    fk_pos_terminal_id: str | None
    pos_terminal_label: str


@dataclass(frozen=True)
class FormControlView:
    id: str
    fk_form_id: str
    form_name: str
    fk_tab_id: str | None
    tab_title: str
    name: str
    type_no: int
    type: str
    caption1: str
    caption2: str
    width: int
    height: int
    location_x: int
    location_y: int
    is_visible: bool
    form_control_function1: str
    form_control_function2: str
    fk_target_form_id: str | None


@dataclass(frozen=True)
class FormControlTabView:
    id: str
    fk_form_control_id: str
    control_name: str
    tab_index: int
    tab_title: str
    tab_tooltip: str
    back_color: str
    fore_color: str
    is_visible: bool


@dataclass(frozen=True)
class PosFormOperationView:
    form_id: str
    form_no: int
    form_name: str
    display_mode: str
    control_count: int
    visible_control_count: int
    hidden_control_count: int
    tab_page_count: int


class PosManagementService:
    """Coordinate POS and dynamic-form related workflows."""

    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_pos_terminals(self, search_text: str | None = None) -> list[PosTerminalView]:
        with self._engine.get_session() as session:
            query = (
                session.query(PosTerminal)
                .filter(PosTerminal.is_deleted.is_(False))
                .order_by(asc(PosTerminal.terminal_code))
            )
            search_value = (search_text or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(
                    PosTerminal.terminal_code.ilike(pattern)
                    | PosTerminal.terminal_name.ilike(pattern)
                    | PosTerminal.terminal_serial_no.ilike(pattern)
                    | PosTerminal.host_name.ilike(pattern)
                    | PosTerminal.ip_address.ilike(pattern)
                )
            rows = query.all()
            return [
                PosTerminalView(
                    id=str(row.id),
                    terminal_code=row.terminal_code or "",
                    terminal_name=row.terminal_name or "",
                    terminal_serial_no=row.terminal_serial_no or "",
                    host_name=row.host_name or "",
                    ip_address=row.ip_address or "",
                    app_mode=row.app_mode or "",
                    software_version=row.software_version or "",
                    is_active=bool(row.is_active),
                    is_online=bool(row.is_online),
                    is_allowed_pull=bool(row.is_allowed_pull),
                    pull_interval_seconds=int(row.pull_interval_seconds or 0),
                )
                for row in rows
            ]

    def save_pos_terminal(
        self,
        payload: dict[str, Any],
        terminal_id: str | None = None,
    ) -> ServiceResult:
        terminal_code = str(payload.get("terminal_code", "")).strip().upper()
        if not terminal_code:
            return ServiceResult(success=False, message="Terminal code is required.")

        store_id = self._resolve_store_id()
        if store_id is None:
            return ServiceResult(success=False, message="Store definition not found.")

        try:
            with self._engine.get_session() as session:
                duplicate = (
                    session.query(PosTerminal)
                    .filter(
                        PosTerminal.fk_store_id == self._as_uuid(store_id),
                        PosTerminal.terminal_code == terminal_code,
                        PosTerminal.is_deleted.is_(False),
                    )
                    .first()
                )
                if duplicate and str(duplicate.id) != str(terminal_id):
                    return ServiceResult(
                        success=False,
                        message=f"Terminal code '{terminal_code}' already exists for this store.",
                    )

                if terminal_id:
                    entity = (
                        session.query(PosTerminal)
                        .filter(
                            PosTerminal.id == self._as_uuid(terminal_id),
                            PosTerminal.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="POS terminal not found.")
                else:
                    entity = PosTerminal()
                    session.add(entity)

                entity.fk_store_id = self._as_uuid(store_id)
                entity.terminal_code = terminal_code
                entity.terminal_name = str(payload.get("terminal_name", "")).strip()
                entity.terminal_serial_no = str(payload.get("terminal_serial_no", "")).strip() or None
                entity.host_name = str(payload.get("host_name", "")).strip() or None
                entity.ip_address = str(payload.get("ip_address", "")).strip() or None
                entity.app_mode = str(payload.get("app_mode", "")).strip() or None
                entity.software_version = str(payload.get("software_version", "")).strip() or None
                entity.is_active = bool(payload.get("is_active", True))
                entity.is_online = bool(payload.get("is_online", False))
                entity.is_allowed_pull = bool(payload.get("is_allowed_pull", True))
                entity.pull_interval_seconds = int(payload.get("pull_interval_seconds", 30))

                return ServiceResult(
                    success=True,
                    message="POS terminal updated successfully."
                    if terminal_id
                    else "POS terminal created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="POS terminal save failed due to a database error.")

    def delete_pos_terminal(self, terminal_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(PosTerminal)
                    .filter(
                        PosTerminal.id == self._as_uuid(terminal_id),
                        PosTerminal.is_deleted.is_(False),
                    )
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="POS terminal not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="POS terminal deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="POS terminal delete failed due to a database error.")

    def list_pos_settings(self, terminal_id: str | None = None) -> list[PosSettingsView]:
        with self._engine.get_session() as session:
            query = (
                session.query(PosSettings, PosTerminal)
                .outerjoin(PosTerminal, PosTerminal.id == PosSettings.fk_pos_terminal_id)
                .filter(PosSettings.is_deleted.is_(False))
                .order_by(asc(PosSettings.pos_no_in_store), asc(PosSettings.name))
            )
            if terminal_id:
                query = query.filter(PosSettings.fk_pos_terminal_id == self._as_uuid(terminal_id))
            rows = query.all()
            return [
                PosSettingsView(
                    id=str(settings.id),
                    fk_pos_terminal_id=(
                        str(settings.fk_pos_terminal_id) if settings.fk_pos_terminal_id else None
                    ),
                    terminal_label=terminal.terminal_code if terminal is not None else "-",
                    pos_no_in_store=int(settings.pos_no_in_store or 0),
                    name=settings.name or "",
                    owner_national_id=settings.owner_national_id or "",
                    owner_tax_id=settings.owner_tax_id or "",
                    mac_address=settings.mac_address or "",
                    backend_type=settings.backend_type or "",
                    backend_ip1=settings.backend_ip1 or "",
                    backend_port1=settings.backend_port1,
                    backend_ip2=settings.backend_ip2 or "",
                    backend_port2=settings.backend_port2,
                    force_to_work_online=bool(settings.force_to_work_online),
                    plu_update_no=int(settings.plu_update_no or 0),
                )
                for settings, terminal in rows
            ]

    def save_pos_settings(
        self,
        payload: dict[str, Any],
        settings_id: str | None = None,
    ) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        if not name:
            return ServiceResult(success=False, message="POS settings name is required.")

        store_id = self._resolve_store_id()
        if store_id is None:
            return ServiceResult(success=False, message="Store definition not found.")

        try:
            with self._engine.get_session() as session:
                if settings_id:
                    entity = (
                        session.query(PosSettings)
                        .filter(
                            PosSettings.id == self._as_uuid(settings_id),
                            PosSettings.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="POS settings record not found.")
                else:
                    entity = PosSettings()
                    session.add(entity)

                entity.fk_store_id = self._as_uuid(store_id)
                terminal_id = payload.get("fk_pos_terminal_id")
                entity.fk_pos_terminal_id = self._as_uuid(terminal_id) if terminal_id else None
                entity.pos_no_in_store = int(payload.get("pos_no_in_store", 1))
                entity.name = name
                entity.owner_national_id = str(payload.get("owner_national_id", "")).strip() or None
                entity.owner_tax_id = str(payload.get("owner_tax_id", "")).strip() or None
                entity.mac_address = str(payload.get("mac_address", "")).strip() or None
                entity.backend_type = str(payload.get("backend_type", "GATE")).strip() or "GATE"
                entity.backend_ip1 = str(payload.get("backend_ip1", "")).strip() or None
                entity.backend_port1 = self._as_optional_int(payload.get("backend_port1"))
                entity.backend_ip2 = str(payload.get("backend_ip2", "")).strip() or None
                entity.backend_port2 = self._as_optional_int(payload.get("backend_port2"))
                entity.force_to_work_online = bool(payload.get("force_to_work_online", False))
                entity.plu_update_no = int(payload.get("plu_update_no", 0))

                return ServiceResult(
                    success=True,
                    message="POS settings updated successfully."
                    if settings_id
                    else "POS settings created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="POS settings save failed due to a database error.")

    def delete_pos_settings(self, settings_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(PosSettings)
                    .filter(
                        PosSettings.id == self._as_uuid(settings_id),
                        PosSettings.is_deleted.is_(False),
                    )
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="POS settings record not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="POS settings deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="POS settings delete failed due to a database error.")

    def list_pos_virtual_keyboards(self, search_text: str | None = None) -> list[PosVirtualKeyboardView]:
        with self._engine.get_session() as session:
            query = (
                session.query(PosVirtualKeyboard)
                .filter(PosVirtualKeyboard.is_deleted.is_(False))
                .order_by(asc(PosVirtualKeyboard.name))
            )
            search_value = (search_text or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(PosVirtualKeyboard.name.ilike(pattern))
            rows = query.all()
            return [
                PosVirtualKeyboardView(
                    id=str(row.id),
                    name=row.name or "",
                    is_active=bool(row.is_active),
                    keyboard_width=int(row.keyboard_width or 0),
                    keyboard_height=int(row.keyboard_height or 0),
                    x_position=int(row.x_position or 0),
                    y_position=int(row.y_position or 0),
                    font_family=row.font_family or "",
                    font_size=int(row.font_size or 0),
                    button_width=int(row.button_width or 0),
                    button_height=int(row.button_height or 0),
                    button_background_color=row.button_background_color or "",
                    button_pressed_color=row.button_pressed_color or "",
                    control_button_width=int(row.control_button_width or 0),
                    control_button_active_color=row.control_button_active_color or "",
                )
                for row in rows
            ]

    def save_pos_virtual_keyboard(
        self,
        payload: dict[str, Any],
        keyboard_id: str | None = None,
    ) -> ServiceResult:
        name = str(payload.get("name", "")).strip().upper()
        if not name:
            return ServiceResult(success=False, message="Virtual keyboard name is required.")

        try:
            with self._engine.get_session() as session:
                duplicate = (
                    session.query(PosVirtualKeyboard)
                    .filter(
                        PosVirtualKeyboard.name == name,
                        PosVirtualKeyboard.is_deleted.is_(False),
                    )
                    .first()
                )
                if duplicate and str(duplicate.id) != str(keyboard_id):
                    return ServiceResult(
                        success=False,
                        message=f"Virtual keyboard '{name}' already exists.",
                    )

                if keyboard_id:
                    entity = (
                        session.query(PosVirtualKeyboard)
                        .filter(
                            PosVirtualKeyboard.id == self._as_uuid(keyboard_id),
                            PosVirtualKeyboard.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="Virtual keyboard not found.")
                else:
                    entity = PosVirtualKeyboard()
                    session.add(entity)

                entity.name = name
                entity.is_active = bool(payload.get("is_active", True))
                entity.keyboard_width = int(payload.get("keyboard_width", 970))
                entity.keyboard_height = int(payload.get("keyboard_height", 315))
                entity.x_position = int(payload.get("x_position", 0))
                entity.y_position = int(payload.get("y_position", 0))
                entity.font_family = str(payload.get("font_family", "Noto Sans CJK JP")).strip()
                entity.font_size = int(payload.get("font_size", 20))
                entity.button_width = int(payload.get("button_width", 80))
                entity.button_height = int(payload.get("button_height", 40))
                entity.button_background_color = str(payload.get("button_background_color", "")).strip()
                entity.button_pressed_color = str(payload.get("button_pressed_color", "")).strip()
                entity.control_button_width = int(payload.get("control_button_width", 120))
                entity.control_button_active_color = str(
                    payload.get("control_button_active_color", "rgb(29, 150, 255)")
                ).strip()

                return ServiceResult(
                    success=True,
                    message="Virtual keyboard updated successfully."
                    if keyboard_id
                    else "Virtual keyboard created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Virtual keyboard save failed due to a database error.",
            )

    def delete_pos_virtual_keyboard(self, keyboard_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(PosVirtualKeyboard)
                    .filter(
                        PosVirtualKeyboard.id == self._as_uuid(keyboard_id),
                        PosVirtualKeyboard.is_deleted.is_(False),
                    )
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="Virtual keyboard not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="Virtual keyboard deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Virtual keyboard delete failed due to a database error.",
            )

    def list_forms(self, search_text: str | None = None) -> list[FormView]:
        with self._engine.get_session() as session:
            query = (
                session.query(Form, PosTerminal)
                .outerjoin(PosTerminal, PosTerminal.id == Form.fk_pos_terminal_id)
                .filter(Form.is_deleted.is_(False))
                .order_by(asc(Form.form_no), asc(Form.name))
            )
            search_value = (search_text or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(
                    Form.name.ilike(pattern)
                    | Form.caption.ilike(pattern)
                    | Form.function.ilike(pattern)
                    | PosTerminal.terminal_code.ilike(pattern)
                    | PosTerminal.terminal_name.ilike(pattern)
                )
            rows = query.all()
            return [
                FormView(
                    id=str(form.id),
                    form_no=int(form.form_no or 0),
                    name=form.name or "",
                    function=form.function or "",
                    caption=form.caption or "",
                    width=form.width,
                    height=form.height,
                    display_mode=form.display_mode or "",
                    need_login=bool(form.need_login),
                    need_auth=bool(form.need_auth),
                    use_virtual_keyboard=bool(form.use_virtual_keyboard),
                    is_visible=bool(form.is_visible),
                    is_startup=bool(form.is_startup),
                    is_shared_across_pos=bool(form.is_shared_across_pos),
                    fk_pos_terminal_id=str(form.fk_pos_terminal_id) if form.fk_pos_terminal_id else None,
                    pos_terminal_label=(
                        f"{terminal.terminal_code} - {terminal.terminal_name or 'Unnamed'}"
                        if terminal is not None
                        else "-"
                    ),
                )
                for form, terminal in rows
            ]

    def save_form(self, payload: dict[str, Any], form_id: str | None = None) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        if not name:
            return ServiceResult(success=False, message="Form name is required.")

        form_no = int(payload.get("form_no", 0))
        if form_no <= 0:
            return ServiceResult(success=False, message="Form number must be greater than zero.")
        is_shared_across_pos = bool(payload.get("is_shared_across_pos", True))
        fk_pos_terminal_id_raw = payload.get("fk_pos_terminal_id")
        fk_pos_terminal_id = (
            str(fk_pos_terminal_id_raw).strip() if fk_pos_terminal_id_raw is not None else ""
        )
        if not is_shared_across_pos and not fk_pos_terminal_id:
            return ServiceResult(
                success=False,
                message="A POS terminal selection is required when the form is not shared.",
            )

        try:
            with self._engine.get_session() as session:
                duplicate = (
                    session.query(Form)
                    .filter(Form.form_no == form_no, Form.is_deleted.is_(False))
                    .first()
                )
                if duplicate and str(duplicate.id) != str(form_id):
                    return ServiceResult(
                        success=False,
                        message=f"Form number '{form_no}' already exists.",
                    )
                if not is_shared_across_pos:
                    terminal = (
                        session.query(PosTerminal)
                        .filter(
                            PosTerminal.id == self._as_uuid(fk_pos_terminal_id),
                            PosTerminal.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if terminal is None:
                        return ServiceResult(
                            success=False,
                            message="Selected POS terminal could not be found.",
                        )

                if form_id:
                    entity = (
                        session.query(Form)
                        .filter(Form.id == self._as_uuid(form_id), Form.is_deleted.is_(False))
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="Form record not found.")
                else:
                    entity = Form()
                    session.add(entity)

                entity.form_no = form_no
                entity.name = name
                entity.function = str(payload.get("function", "")).strip() or None
                entity.caption = str(payload.get("caption", "")).strip() or None
                entity.width = self._as_optional_int(payload.get("width"))
                entity.height = self._as_optional_int(payload.get("height"))
                entity.display_mode = str(payload.get("display_mode", "MAIN")).strip() or "MAIN"
                entity.need_login = bool(payload.get("need_login", False))
                entity.need_auth = bool(payload.get("need_auth", False))
                entity.use_virtual_keyboard = bool(payload.get("use_virtual_keyboard", False))
                entity.is_visible = bool(payload.get("is_visible", True))
                entity.is_startup = bool(payload.get("is_startup", False))
                entity.is_shared_across_pos = is_shared_across_pos
                entity.fk_pos_terminal_id = (
                    None if is_shared_across_pos else self._as_uuid(fk_pos_terminal_id)
                )

                return ServiceResult(
                    success=True,
                    message="Form updated successfully." if form_id else "Form created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="Form save failed due to a database error.")

    def delete_form(self, form_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(Form)
                    .filter(Form.id == self._as_uuid(form_id), Form.is_deleted.is_(False))
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="Form record not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="Form deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="Form delete failed due to a database error.")

    def list_form_controls(self, form_id: str | None = None) -> list[FormControlView]:
        with self._engine.get_session() as session:
            query = (
                session.query(FormControl, Form, FormControlTab)
                .join(Form, Form.id == FormControl.fk_form_id)
                .outerjoin(FormControlTab, FormControlTab.id == FormControl.fk_tab_id)
                .filter(FormControl.is_deleted.is_(False), Form.is_deleted.is_(False))
                .order_by(asc(Form.form_no), asc(FormControl.location_y), asc(FormControl.location_x))
            )
            if form_id:
                query = query.filter(FormControl.fk_form_id == self._as_uuid(form_id))
            rows = query.all()
            return [
                FormControlView(
                    id=str(control.id),
                    fk_form_id=str(control.fk_form_id),
                    form_name=form.name or "",
                    fk_tab_id=str(control.fk_tab_id) if control.fk_tab_id else None,
                    tab_title=tab.tab_title if tab is not None else "",
                    name=control.name or "",
                    type_no=int(control.type_no or 0),
                    type=control.type or "",
                    caption1=control.caption1 or "",
                    caption2=control.caption2 or "",
                    width=int(control.width or 0),
                    height=int(control.height or 0),
                    location_x=int(control.location_x or 0),
                    location_y=int(control.location_y or 0),
                    is_visible=bool(control.is_visible),
                    form_control_function1=control.form_control_function1 or "",
                    form_control_function2=control.form_control_function2 or "",
                    fk_target_form_id=str(control.fk_target_form_id)
                    if control.fk_target_form_id
                    else None,
                )
                for control, form, tab in rows
            ]

    def save_form_control(
        self,
        payload: dict[str, Any],
        control_id: str | None = None,
    ) -> ServiceResult:
        form_id = str(payload.get("fk_form_id", "")).strip()
        control_name = str(payload.get("name", "")).strip()
        control_type = str(payload.get("type", "")).strip()
        if not form_id:
            return ServiceResult(success=False, message="Form selection is required.")
        if not control_name:
            return ServiceResult(success=False, message="Control name is required.")
        if not control_type:
            return ServiceResult(success=False, message="Control type is required.")

        try:
            with self._engine.get_session() as session:
                if control_id:
                    entity = (
                        session.query(FormControl)
                        .filter(
                            FormControl.id == self._as_uuid(control_id),
                            FormControl.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="Form control record not found.")
                else:
                    entity = FormControl()
                    session.add(entity)

                entity.fk_form_id = self._as_uuid(form_id)
                entity.fk_tab_id = self._as_uuid(payload.get("fk_tab_id")) if payload.get("fk_tab_id") else None
                entity.name = control_name
                entity.type_no = int(payload.get("type_no", 0))
                entity.type = control_type
                entity.caption1 = str(payload.get("caption1", "")).strip() or None
                entity.caption2 = str(payload.get("caption2", "")).strip() or None
                entity.width = int(payload.get("width", 0))
                entity.height = int(payload.get("height", 0))
                entity.location_x = int(payload.get("location_x", 0))
                entity.location_y = int(payload.get("location_y", 0))
                entity.is_visible = bool(payload.get("is_visible", True))
                entity.form_control_function1 = str(payload.get("form_control_function1", "")).strip() or None
                entity.form_control_function2 = str(payload.get("form_control_function2", "")).strip() or None
                target_form_id = payload.get("fk_target_form_id")
                entity.fk_target_form_id = self._as_uuid(target_form_id) if target_form_id else None

                return ServiceResult(
                    success=True,
                    message="Form control updated successfully."
                    if control_id
                    else "Form control created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="Form control save failed due to a database error.")

    def delete_form_control(self, control_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(FormControl)
                    .filter(
                        FormControl.id == self._as_uuid(control_id),
                        FormControl.is_deleted.is_(False),
                    )
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="Form control record not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="Form control deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(success=False, message="Form control delete failed due to a database error.")

    def list_form_control_tabs(self, form_id: str | None = None) -> list[FormControlTabView]:
        with self._engine.get_session() as session:
            query = (
                session.query(FormControlTab, FormControl, Form)
                .join(FormControl, FormControl.id == FormControlTab.fk_form_control_id)
                .join(Form, Form.id == FormControl.fk_form_id)
                .filter(
                    FormControlTab.is_deleted.is_(False),
                    FormControl.is_deleted.is_(False),
                    Form.is_deleted.is_(False),
                )
                .order_by(asc(Form.form_no), asc(FormControl.name), asc(FormControlTab.tab_index))
            )
            if form_id:
                query = query.filter(Form.id == self._as_uuid(form_id))
            rows = query.all()
            return [
                FormControlTabView(
                    id=str(tab.id),
                    fk_form_control_id=str(tab.fk_form_control_id),
                    control_name=control.name or "",
                    tab_index=int(tab.tab_index or 0),
                    tab_title=tab.tab_title or "",
                    tab_tooltip=tab.tab_tooltip or "",
                    back_color=tab.back_color or "",
                    fore_color=tab.fore_color or "",
                    is_visible=bool(tab.is_visible),
                )
                for tab, control, _ in rows
            ]

    def save_form_control_tab(
        self,
        payload: dict[str, Any],
        tab_id: str | None = None,
    ) -> ServiceResult:
        control_id = str(payload.get("fk_form_control_id", "")).strip()
        tab_title = str(payload.get("tab_title", "")).strip()
        if not control_id:
            return ServiceResult(success=False, message="Parent tab control selection is required.")
        if not tab_title:
            return ServiceResult(success=False, message="Tab title is required.")

        try:
            with self._engine.get_session() as session:
                if tab_id:
                    entity = (
                        session.query(FormControlTab)
                        .filter(
                            FormControlTab.id == self._as_uuid(tab_id),
                            FormControlTab.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if entity is None:
                        return ServiceResult(success=False, message="Form control tab record not found.")
                else:
                    entity = FormControlTab()
                    session.add(entity)

                entity.fk_form_control_id = self._as_uuid(control_id)
                entity.tab_index = int(payload.get("tab_index", 0))
                entity.tab_title = tab_title
                entity.tab_tooltip = str(payload.get("tab_tooltip", "")).strip() or None
                entity.back_color = str(payload.get("back_color", "")).strip() or None
                entity.fore_color = str(payload.get("fore_color", "")).strip() or None
                entity.is_visible = bool(payload.get("is_visible", True))

                return ServiceResult(
                    success=True,
                    message="Form control tab updated successfully."
                    if tab_id
                    else "Form control tab created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Form control tab save failed due to a database error.",
            )

    def delete_form_control_tab(self, tab_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                entity = (
                    session.query(FormControlTab)
                    .filter(
                        FormControlTab.id == self._as_uuid(tab_id),
                        FormControlTab.is_deleted.is_(False),
                    )
                    .first()
                )
                if entity is None:
                    return ServiceResult(success=False, message="Form control tab record not found.")
                entity.is_deleted = True
                return ServiceResult(success=True, message="Form control tab deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                success=False,
                message="Form control tab delete failed due to a database error.",
            )

    def list_pos_form_operations(self) -> list[PosFormOperationView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(
                    Form.id,
                    Form.form_no,
                    Form.name,
                    Form.display_mode,
                    func.count(FormControl.id),
                    func.sum(case((FormControl.is_visible.is_(True), 1), else_=0)),
                    func.sum(case((FormControl.is_visible.is_(False), 1), else_=0)),
                    func.count(FormControlTab.id),
                )
                .outerjoin(
                    FormControl,
                    (FormControl.fk_form_id == Form.id) & FormControl.is_deleted.is_(False),
                )
                .outerjoin(
                    FormControlTab,
                    (FormControlTab.fk_form_control_id == FormControl.id)
                    & FormControlTab.is_deleted.is_(False),
                )
                .filter(Form.is_deleted.is_(False))
                .group_by(Form.id, Form.form_no, Form.name, Form.display_mode)
                .order_by(asc(Form.form_no), asc(Form.name))
                .all()
            )
            return [
                PosFormOperationView(
                    form_id=str(form_id),
                    form_no=int(form_no or 0),
                    form_name=form_name or "",
                    display_mode=display_mode or "",
                    control_count=int(control_count or 0),
                    visible_control_count=int(visible_count or 0),
                    hidden_control_count=int(hidden_count or 0),
                    tab_page_count=int(tab_count or 0),
                )
                for (
                    form_id,
                    form_no,
                    form_name,
                    display_mode,
                    control_count,
                    visible_count,
                    hidden_count,
                    tab_count,
                ) in rows
            ]

    def list_pos_terminal_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(PosTerminal)
                .filter(PosTerminal.is_deleted.is_(False))
                .order_by(asc(PosTerminal.terminal_code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.terminal_code} - {row.terminal_name or 'Unnamed'}")
                for row in rows
            ]

    def list_form_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Form)
                .filter(Form.is_deleted.is_(False))
                .order_by(asc(Form.form_no), asc(Form.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=f"{row.form_no} - {row.name}") for row in rows]

    def list_tab_control_lookups(self, form_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(FormControl, Form)
                .join(Form, Form.id == FormControl.fk_form_id)
                .filter(
                    FormControl.is_deleted.is_(False),
                    Form.is_deleted.is_(False),
                    FormControl.type.ilike("TABCONTROL"),
                )
                .order_by(asc(Form.form_no), asc(FormControl.name))
            )
            if form_id:
                query = query.filter(FormControl.fk_form_id == self._as_uuid(form_id))
            rows = query.all()
            return [
                LookupItem(
                    id=str(control.id),
                    label=f"{form.form_no} - {form.name} :: {control.name}",
                )
                for control, form in rows
            ]

    def list_form_controls_for_form(self, form_id: str) -> list[FormControlView]:
        return self.list_form_controls(form_id=form_id)

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
            return str(store.id) if store is not None else None

    @staticmethod
    def _as_uuid(value: str | None) -> UUID | None:
        if value is None:
            return None
        return UUID(str(value))

    @staticmethod
    def _as_optional_int(value: Any) -> int | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        return int(raw)
