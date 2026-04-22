"""
SaleFlex.PyPOS - Database Initial Data

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

from data_layer.model import Cashier


from core.logger import get_logger

logger = get_logger(__name__)

def _insert_admin_cashier(session) -> Cashier:
    """
    Insert default cashiers if not exists.
    Creates admin user and a standard cashier for initial setup.
    """
    admin_exists = session.query(Cashier).filter_by(user_name="admin").first()
    if not admin_exists:
        admin_cashier = Cashier(
            no=1,
            user_name="admin",
            name="Ferhat",
            last_name="Mousavi",
            password="admin",  # TODO: Should be hashed in real application
            identity_number="A00001",
            description="System administrator",
            is_administrator=True,
            is_manager=False,
            is_active=True
        )
        session.add(admin_cashier)
        session.flush()  # To get the ID
        logger.info("✓ Default cashier 'Ferhat Mousavi' added (password: admin)")
    else:
        admin_cashier = admin_exists

    cashier_exists = session.query(Cashier).filter_by(user_name="jdoe").first()
    if not cashier_exists:
        standard_cashier = Cashier(
            no=2,
            user_name="jdoe",
            name="John",
            last_name="Doe",
            password="1234",
            identity_number="C00002",
            description="Standard cashier",
            is_administrator=False,
            is_manager=False,
            is_active=True
        )
        session.add(standard_cashier)
        session.flush()
        logger.info("✓ Default cashier 'John Doe' added (password: 1234)")

    jpace_exists = session.query(Cashier).filter_by(user_name="jpace").first()
    legacy_manager = session.query(Cashier).filter_by(user_name="manager").first()

    if legacy_manager and not jpace_exists:
        legacy_manager.user_name = "jpace"
        legacy_manager.name = "Jamie"
        legacy_manager.last_name = "Pace"
        legacy_manager.description = "Store manager"
        legacy_manager.is_administrator = False
        legacy_manager.is_manager = True
        legacy_manager.is_active = True
        session.flush()
        logger.info("✓ Legacy manager user migrated to 'jpace'")
    elif not jpace_exists:
        manager_cashier = Cashier(
            no=3,
            user_name="jpace",
            name="Jamie",
            last_name="Pace",
            password="jpace",
            identity_number="M00003",
            description="Store manager",
            is_administrator=False,
            is_manager=True,
            is_active=True,
        )
        session.add(manager_cashier)
        session.flush()
        logger.info("✓ Default manager user 'jpace' added")

    return admin_cashier