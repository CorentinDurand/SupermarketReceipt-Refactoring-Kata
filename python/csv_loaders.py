import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from model_objects import Coupon, Product, ProductUnit, SpecialOfferType


def read_catalog(catalog_file: Path, catalog):
    if not catalog_file.exists():
        return catalog
    with open(catalog_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            unit = ProductUnit[row["unit"]]
            price = Decimal(row["price"])
            product = Product(name, unit)
            catalog.add_product(product, price)
    return catalog


def read_offers(offers_file: Path, teller, catalog):
    if not offers_file.exists():
        return
    with open(offers_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            offer_type = SpecialOfferType[row["offer"]]
            argument_raw = row.get("argument", "")
            argument = float(argument_raw) if argument_raw else None
            product = catalog.products[name]
            teller.add_special_offer(offer_type, product, argument)


def read_bundle_offers(bundles_file: Path, teller, catalog) -> int:
    """
    Expected CSV format:
      bundle_name,discount_percent,items
      starter_pack,10,toothbrush:1;toothpaste:1
    """
    if not bundles_file.exists():
        return 0

    count = 0
    with open(bundles_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items = (row.get("items") or "").strip()
            if not items:
                continue

            items_required = {}
            for item in items.split(";"):
                item = item.strip()
                if not item:
                    continue
                product_name, qty = item.split(":", 1)
                product = catalog.products.get(product_name.strip())
                if not product:
                    raise ValueError(f"Unknown product '{product_name}' in {bundles_file}")
                items_required[product] = Decimal(qty.strip())

            discount_percent = Decimal((row.get("discount_percent") or "10").strip())
            teller.add_bundle_offer(items_required, discount_percent=discount_percent)
            count += 1

    return count


def read_coupons(coupons_file: Path, catalog):
    """
    Expected CSV format:
      name,product,required_qty,discounted_qty,discount_percent,valid_from,valid_to,description
      orange_juice_coupon,orange juice,6,6,50,2025-11-13,2025-11-15,orange juice coupon
    """
    if not coupons_file.exists():
        return []

    coupons = []
    with open(coupons_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_name = (row.get("product") or "").strip()
            product = catalog.products.get(product_name)
            if not product:
                raise ValueError(f"Unknown product '{product_name}' in {coupons_file}")

            coupons.append(
                Coupon(
                    product=product,
                    required_qty=Decimal(row["required_qty"]),
                    discounted_qty=Decimal(row["discounted_qty"]),
                    discount_percent=Decimal(row["discount_percent"]),
                    valid_from=date.fromisoformat(row["valid_from"]),
                    valid_to=date.fromisoformat(row["valid_to"]),
                    description=(row.get("description") or row.get("name") or "coupon").strip(),
                )
            )
    return coupons


def read_cart(cart_file: Path, catalog):
    """
    Expected CSV format:
      name,quantity
      toothpaste,5
      apples,1.2
    """
    if not cart_file.exists():
        return []

    items = []
    with open(cart_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            qty = Decimal(str(row["quantity"]).strip())
            product = catalog.products.get(name)
            if not product:
                raise ValueError(f"Unknown product '{name}' in {cart_file}")
            items.append((product, qty))
    return items

