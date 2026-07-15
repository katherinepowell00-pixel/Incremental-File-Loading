"""
Run once to bootstrap the "OLTP system" — writes full snapshot files for
stores and products (rarely change) and an initial customer batch, then
saves state so incremental runs can reference these entities.

Usage:
    python seed.py --out ./output --n-customers 500 --n-products 200
"""
import argparse
import csv
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
import state

fake = Faker()

CATEGORIES = {
    "Furniture": ["Chairs", "Tables", "Bookcases"],
    "Technology": ["Phones", "Accessories", "Copiers"],
    "Office Supplies": ["Binders", "Paper", "Storage"],
}
CHANNELS = ["online", "retail"]
REGIONS = ["West", "East", "Central", "South"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]


def gen_stores(n: int) -> list[dict]:
    stores = []
    for i in range(n):
        stores.append({
            "store_id": f"ST-{i+1:03d}",
            "store_name": f"{fake.city()} {random.choice(CHANNELS).title()} Store",
            "region": random.choice(REGIONS),
            "channel": random.choice(CHANNELS),
        })
    return stores


def gen_products(n: int) -> list[dict]:
    products = []
    for i in range(n):
        category = random.choice(list(CATEGORIES))
        cost = round(random.uniform(5, 400), 2)
        products.append({
            "product_id": f"PR-{i+1:05d}",
            "product_name": fake.catch_phrase(),
            "category": category,
            "subcategory": random.choice(CATEGORIES[category]),
            "brand": fake.company(),
            "unit_cost": cost,
            "unit_price": round(cost * random.uniform(1.2, 2.5), 2),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    return products


def gen_customers(n: int) -> list[dict]:
    customers = []
    for _ in range(n):
        customers.append({
            "customer_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "country": "US",
            "segment": random.choice(SEGMENTS),
            "record_type": "I",  # insert
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    return customers


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="./output")
    parser.add_argument("--n-customers", type=int, default=500)
    parser.add_argument("--n-products", type=int, default=200)
    parser.add_argument("--n-stores", type=int, default=15)
    args = parser.parse_args()

    out = Path(args.out)

    stores = gen_stores(args.n_stores)
    products = gen_products(args.n_products)
    customers = gen_customers(args.n_customers)

    write_csv(stores, out / "stores" / "stores_seed.csv")
    write_csv(products, out / "products" / "products_seed.csv")
    write_csv(customers, out / "customers" / f"customers_{datetime.now():%Y%m%d}.csv")

    state.save_stores(stores)
    state.save_products(products)
    state.save_customers(customers)

    print(f"Seeded {len(stores)} stores, {len(products)} products, {len(customers)} customers")


if __name__ == "__main__":
    main()


    