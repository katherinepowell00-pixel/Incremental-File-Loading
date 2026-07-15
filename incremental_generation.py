import argparse
import csv
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
from faker import Faker
import state as state   # your renamed state module

fake = Faker()

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
STATUSES = ["placed", "shipped", "delivered", "cancelled"]

s3 = boto3.client("s3")


def upload_to_s3(local_path: Path, bucket: str, prefix: str):
    key = f"{prefix}/{local_path.name}"
    s3.upload_file(str(local_path), bucket, key)
    print(f"Uploaded to s3://{bucket}/{key}")


def write_csv(records: list[dict], path: Path) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def gen_customer_delta(customers: list[dict], n_new: int, n_updated: int) -> list[dict]:
    delta = []
    now = datetime.now(timezone.utc).isoformat()

    for _ in range(n_new):
        record = {
            "customer_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "country": "US",
            "segment": random.choice(SEGMENTS),
            "record_type": "I",
            "updated_at": now,
        }
        customers.append(record)
        delta.append(record)

    if customers and n_updated:
        for record in random.sample(customers, min(n_updated, len(customers))):
            record["city"] = fake.city()
            record["state"] = fake.state_abbr()
            record["segment"] = random.choice(SEGMENTS)
            record["record_type"] = "U"
            record["updated_at"] = now
            delta.append(record)

    return delta


def gen_orders(customers, products, stores, n_orders, order_date):
    orders = []
    for _ in range(n_orders):
        order_id = str(uuid.uuid4())
        customer = random.choice(customers)
        n_lines = random.randint(1, 4)
        for line_num in range(1, n_lines + 1):
            product = random.choice(products)
            store = random.choice(stores)
            quantity = random.randint(1, 5)
            discount = round(random.choice([0, 0, 0, 0.1, 0.15]), 2)
            unit_price = float(product["unit_price"])
            net_amount = round(unit_price * quantity * (1 - discount), 2)
            orders.append({
                "order_id": order_id,
                "order_line_id": f"{order_id}-{line_num}",
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "store_id": store["store_id"],
                "order_date": order_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_amount": discount,
                "net_amount": net_amount,
                "order_status": random.choice(STATUSES),
            })
    return orders


def gen_inventory_snapshot(products, stores, snapshot_date):
    rows = []
    for store in stores:
        for product in products:
            rows.append({
                "snapshot_date": snapshot_date,
                "store_id": store["store_id"],
                "product_id": product["product_id"],
                "quantity_on_hand": random.randint(0, 500),
                "reorder_point": random.randint(20, 100),
            })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="./output")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--new-customers", type=int, default=10)
    parser.add_argument("--updated-customers", type=int, default=15)
    parser.add_argument("--n-orders", type=int, default=300)
    parser.add_argument("--bucket", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    date_compact = args.date.replace("-", "")

    customers = state.load_customers()
    products = state.load_products()
    stores = state.load_stores()

    if not (customers and products and stores):
        raise SystemExit("No state found — run seed.py first.")

    # Generate data
    customer_delta = gen_customer_delta(customers, args.new_customers, args.updated_customers)
    orders = gen_orders(customers, products, stores, args.n_orders, args.date)
    inventory = gen_inventory_snapshot(products, stores, args.date)

    # Write local files
    cust_path = out / "customers" / f"dt={args.date}" / f"customers_{date_compact}.csv"
    ord_path = out / "orders" / f"dt={args.date}" / f"orders_{date_compact}.csv"
    inv_path = out / "inventory" / f"dt={args.date}" / f"inventory_{date_compact}.csv"

    write_csv(customer_delta, cust_path)
    write_csv(orders, ord_path)
    write_csv(inventory, inv_path)

    # Upload to S3
    upload_to_s3(cust_path, args.bucket, f"customers/dt={args.date}")
    upload_to_s3(ord_path, args.bucket, f"orders/dt={args.date}")
    upload_to_s3(inv_path, args.bucket, f"inventory/dt={args.date}")

    # Persist updated customers
    state.save_customers(customers)

    print(f"{args.date}: {len(customer_delta)} customer deltas, "
          f"{len(orders)} order lines, {len(inventory)} inventory rows")


if __name__ == "__main__":
    main()
