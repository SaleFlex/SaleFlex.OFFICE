"""Service layer package for SaleFlex.OFFICE."""

from office.service.pipos_bootstrap_service import BootstrapTopic, PyPosBootstrapService

__all__ = [
    "BootstrapTopic",
    "PyPosBootstrapService",
]
