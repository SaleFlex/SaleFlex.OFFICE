![Python 3.13](https://img.shields.io/badge/python-%3E=_3.13-success.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.11.0-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.48-green.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.3-yellow.svg)
![License](https://img.shields.io/badge/license-AGPLv3-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0a2-orange.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)

[SaleFlex Ecosystem](https://github.com/SaleFlex) | [SaleFlex.PyPOS](https://github.com/SaleFlex/SaleFlex.PyPOS) | **[SaleFlex.OFFICE](https://github.com/SaleFlex/SaleFlex.OFFICE)** | [SaleFlex.GATE](https://github.com/SaleFlex/SaleFlex.GATE) | [SaleFlex.KITCHEN](https://github.com/SaleFlex/SaleFlex.KITCHEN) | [SaleFlex.mPOS](https://github.com/SaleFlex/SaleFlex.mPOS)

# SaleFlex.OFFICE

**SaleFlex.OFFICE** is the back-office management application of the SaleFlex ecosystem - a PySide6 desktop application that gives store managers and administrators full control over products, campaigns, customers, loyalty programs, POS terminals, and transaction data.

It acts as the local coordination hub between your POS terminals and the central SaleFlex.GATE cloud, keeping operations running smoothly even when internet connectivity is unstable.

> Developed and operated by **[Mousavi.Tech](https://mousavi.tech)**

---

## Who Is This For?

SaleFlex.OFFICE is built for:

- **Store managers and administrators** who need a desktop back-office to manage products, pricing, campaigns, and cashiers without touching the POS terminal.
- **Multi-terminal retailers** who need a single coordination point for several POS devices in the same store.
- **Businesses already using SaleFlex.PyPOS** who want to manage master data, review transactions, and sync to the cloud from a dedicated management workstation.
- **Tech-forward teams** who want a self-hosted, open-source back-office they can extend and integrate with their existing ERP or accounting systems.

---

## Community Edition

SaleFlex.OFFICE is fully **open source** under the [GNU Affero General Public License v3.0 (AGPLv3)](LICENSE).

The Community Edition includes everything you need to manage a store:

- Product, variant, barcode, and pricing management
- Campaign and promotion management (types, rules, products, usage tracking)
- Customer management with loyalty programs, tiers, earn/redeem rules, and point history
- Cashier management with role-based access and performance metrics
- POS terminal management and configuration
- Warehouse management (stock levels, movements, adjustments)
- Transaction viewer - read-only view of all POS transactions, payments, and discounts
- Data sync and backup monitoring (outbox queue, GATE notifications, sent history)
- System settings (mode, store/office codes, POS server, GATE integration)
- Built-in REST API server for SaleFlex.PyPOS terminal bootstrap and data push
- Self-hosted - your data stays with you

Anyone can clone, run, and modify SaleFlex.OFFICE for their own needs. Contributions are welcome.

---

## Commercial Services

Need professional support or custom features? We offer:

- **Custom development** - tailored features, integrations, and workflows built for your business.
- **Implementation & onboarding** - hands-on setup, hardware configuration, and staff training.
- **Priority support** - dedicated support channels with guaranteed response times.
- **Integration services** - connecting SaleFlex.OFFICE to your existing ERP, accounting, loyalty, or payment systems.

> Contact us at [saleflex.pro](https://saleflex.pro) for commercial enquiries.

---

## Managed Cloud

Pair SaleFlex.OFFICE with **SaleFlex Cloud** (coming soon) for a fully managed backend:

- No server to manage - we handle updates, backups, and scaling.
- One-click OFFICE and GATE backend provisioning.
- Built-in sales, stock, and KPI reporting dashboards.
- Enterprise-grade security and compliance.
- Multi-region availability.

> Join the waitlist at [saleflex.net](https://saleflex.net) to be notified when Managed Cloud launches.

---

## Download Ready Builds

Pre-packaged installers are currently in preparation. Once available, you will be able to download ready-to-run builds for Windows and Linux.

**Until then, get started with:**

```bash
git clone https://github.com/SaleFlex/SaleFlex.OFFICE.git
cd SaleFlex.OFFICE

# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python saleflex.py
```

**Default login credentials:**

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin` | Administrator |
| `jdoe` | `1234` | Manager |

> **Requirements:** Python 3.13+ - PySide6 6.11+ - SQLAlchemy 2.0+ - Windows or Linux

---

## Screenshots

> Screenshots coming soon. The module launcher, product management, campaign management, transaction viewer, and sync dashboard will be showcased here.

---

## Demo Video

> A demo video is being prepared and will be published here and on the SaleFlex YouTube channel shortly.

---

## Roadmap

### Done
- Application startup with splash screen and bootstrap progress
- Login screen with role-based access (admin, manager)
- Module launcher with fullscreen operational layout
- Product management (CRUD for products, variants, barcodes, attributes, manufacturers, units)
- Campaign management (types, rules, campaign products, usage tracking)
- Customer management (CRUD, segments, loyalty, coupon history)
- Loyalty management (program, tiers, earn rules, redemption policies, point transactions)
- Cashier management (CRUD, performance targets, transaction metrics)
- POS terminal management (CRUD, settings, virtual keyboard definitions)
- Form management (CRUD for dynamic POS forms, terminal targeting)
- Warehouse management (locations, stock levels, movements, adjustments)
- Definitions management (countries, regions, cities, currencies, VAT, payment types)
- Transaction viewer (read-only, per-terminal tabs, product/payment/discount detail)
- Data sync and backup monitor (outbox queue, failed items, sent history, GATE notifications)
- System settings (mode, store/office codes, POS server bind, GATE configuration)
- Built-in Flask REST API (health, POS init, transaction push, closure push, sequence sync)
- Multi-terminal support with independent per-POS sequence counters
- Logout support without restarting the REST server
- Post-closure master-data refresh propagation to POS terminals

### In Progress
- GATE background sync worker
- Advanced reporting dashboards

### Planned
- CSV/XML bulk import for products, campaigns, and loyalty definitions
- CSV/PDF export for reports
- Sales, stock, and KPI dashboards
- Security hardening and PCI DSS compliance
- Pre-packaged Windows and Linux installers
- SaleFlex Cloud (managed hosting)

---

## Related Projects

| Project | Description |
|---------|-------------|
| [SaleFlex.PyPOS](https://github.com/SaleFlex/SaleFlex.PyPOS) | Python / PySide6 touch POS terminal |
| [SaleFlex.GATE](https://github.com/SaleFlex/SaleFlex.GATE) | Central hub and API gateway |
| [SaleFlex.KITCHEN](https://github.com/SaleFlex/SaleFlex.KITCHEN) | Kitchen display system |
| [SaleFlex.mPOS](https://github.com/SaleFlex/SaleFlex.mPOS) | Android mobile POS |
| [SaleFlex.POS](https://github.com/SaleFlex/SaleFlex.POS) | Legacy .NET POS client |

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**. See [LICENSE](LICENSE) for details.

---

## Contributors

<table>
<tr>
    <td align="center">
        <a href="https://github.com/ferhat-mousavi">
            <img src="https://avatars.githubusercontent.com/u/5930760?v=4" width="100;" alt="Ferhat Mousavi"/>
            <br />
            <sub><b>Ferhat Mousavi</b></sub>
        </a>
    </td>
</tr>
</table>

## Donation and Support

If you find SaleFlex.OFFICE useful and want to support its development:

- **USDT / BUSD / ETH:** `0xa5a87a939bfcd492f056c26e4febe102ea599b5b`
- **BTC:** `15qyZpi6HjYyVhKKBsCbZSXU4bLdVJ8Phe`
- **SOL:** `Gt3bDczPcJvfBeg9TTBrBJGSHLJVkvnSSTov8W3QMpQf`