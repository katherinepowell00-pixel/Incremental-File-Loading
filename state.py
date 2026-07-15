"""
Persists the pool of customer_ids / product_ids / store_ids already
"in the system" so daily incremental runs can reference existing entities
(for updates and for FK integrity in orders) instead of inventing orphans.
"""
import json
from pathlib import Path

STATE_DIR = Path(__file__).parent / "_state"
STATE_DIR.mkdir(exist_ok=True)

CUSTOMERS_FILE = STATE_DIR / "customers.json"
PRODUCTS_FILE = STATE_DIR / "products.json"
STORES_FILE = STATE_DIR / "stores.json"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save(path: Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        json.dump(records, f, indent=2, default=str)


def load_customers() -> list[dict]:
    return load(CUSTOMERS_FILE)


def save_customers(records: list[dict]) -> None:
    save(CUSTOMERS_FILE, records)


def load_products() -> list[dict]:
    return load(PRODUCTS_FILE)


def save_products(records: list[dict]) -> None:
    save(PRODUCTS_FILE, records)


def load_stores() -> list[dict]:
    return load(STORES_FILE)


def save_stores(records: list[dict]) -> None:
    save(STORES_FILE, records)