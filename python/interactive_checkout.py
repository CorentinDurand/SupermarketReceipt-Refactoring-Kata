from datetime import date
from decimal import Decimal
from pathlib import Path

from cli_prompts import parse_date, parse_decimal, prompt_with_default, yes_no
from csv_loaders import read_bundle_offers, read_cart, read_catalog, read_coupons, read_offers
from model_objects import LoyaltyAccount
from receipt_printer import ReceiptPrinter
from shopping_cart import ShoppingCart
from teller import Teller
from fake_catalog import FakeCatalog


def build_cart(catalog):
    cart = ShoppingCart()
    cart_file = Path("cart.csv")
    if cart_file.exists():
        try:
            for product, qty in read_cart(cart_file, catalog):
                cart.add_item_quantity(product, qty)
            if yes_no("Loaded cart.csv. Use it as starting cart? (y/n)", "y"):
                return cart
            cart = ShoppingCart()
        except Exception as exc:
            print(f"Failed to read {cart_file}: {exc}")

    print("Add items to your cart. Enter 'done' when finished.")
    print("Format: <product_name> <quantity> (example: toothpaste 5)")
    print("Tip: press Enter on an empty line to use a typical demo cart.")
    while True:
        raw = input("> ").strip()
        if raw == "":
            defaults = [("toothpaste", "5"), ("toothbrush", "1"), ("apples", "1.2")]
            for name, qty in defaults:
                product = catalog.products.get(name)
                if product:
                    cart.add_item_quantity(product, Decimal(qty))
            break
        if not raw:
            continue
        if raw.lower() == "done":
            break
        parts = raw.split()
        if len(parts) < 2:
            print("Please enter both a product name and quantity.")
            continue
        name = " ".join(parts[:-1])
        quantity = Decimal(parts[-1])
        product = catalog.products.get(name)
        if not product:
            print(f"Unknown product '{name}'. Known products: {', '.join(sorted(catalog.products.keys()))}")
            continue
        cart.add_item_quantity(product, quantity)
    return cart


def configure_bundle_offers(teller, catalog):
    bundles_file = Path("bundles.csv")
    loaded = 0
    try:
        loaded = read_bundle_offers(bundles_file, teller, catalog)
    except Exception as exc:
        print(f"Failed to read {bundles_file}: {exc}")

    raw = "n" if loaded else "y"
    while True:
        if not yes_no("Add a bundle offer? (y/n)", raw):
            return

        print("Define bundle items. Enter 'done' when finished.")
        print("Tip: press Enter on an empty line to use a typical bundle (toothbrush 1 + toothpaste 1).")
        items_required = {}
        while True:
            raw_item = input("bundle> ").strip()
            if raw_item == "":
                defaults = [("toothbrush", "1"), ("toothpaste", "1")]
                for name, qty in defaults:
                    product = catalog.products.get(name)
                    if product:
                        items_required[product] = Decimal(qty)
                break
            if raw_item.lower() in ("done", "n", "no"):
                break
            parts = raw_item.split()
            if len(parts) < 2:
                print("Format: <product_name> <quantity>")
                continue
            name = " ".join(parts[:-1])
            qty = Decimal(parts[-1])
            product = catalog.products.get(name)
            if not product:
                print(f"Unknown product '{name}'.")
                continue
            items_required[product] = qty

        if not items_required:
            print("Bundle ignored (no items).")
            continue

        discount_percent = parse_decimal("Bundle discount percent", "10") or Decimal("10")
        teller.add_bundle_offer(items_required, discount_percent=discount_percent)
        print("Bundle offer added.")


def configure_coupon(teller, catalog):
    coupons_file = Path("coupons.csv")
    try:
        coupons = read_coupons(coupons_file, catalog)
    except Exception as exc:
        print(f"Failed to read {coupons_file}: {exc}")
        coupons = []

    if coupons:
        print("Available coupons:")
        for idx, coupon in enumerate(coupons, start=1):
            print(
                f"  {idx}. {coupon.description} ({coupon.product.name}) "
                f"[{coupon.valid_from.isoformat()}..{coupon.valid_to.isoformat()}]"
            )
        raw = prompt_with_default("Choose a coupon number (or 0 for none):", "1").strip()
        choice = int(raw) if raw.isdigit() else 0
        if choice <= 0:
            return
        if choice > len(coupons):
            print("Invalid choice. No coupon used.")
            return
        teller.use_coupon(coupons[choice - 1])
        print("Coupon set for this checkout.")
        return

    if not yes_no("Use a coupon for this checkout? (y/n)", "n"):
        return

    name = prompt_with_default("Coupon product name:", "orange juice").strip()
    product = catalog.products.get(name)
    if not product:
        print(f"Unknown product '{name}'. Coupon ignored.")
        return

    required_qty = parse_decimal("Required quantity (e.g., 6):", "6")
    discounted_qty = parse_decimal("Discounted quantity (e.g., 6):", "6")
    discount_percent = parse_decimal("Discount percent (e.g., 50):", "50")
    valid_from = parse_date("Valid from (YYYY-MM-DD):", "2025-12-13")
    valid_to = parse_date("Valid to (YYYY-MM-DD):", "2025-12-15")
    description = prompt_with_default("Coupon description (optional):", "orange juice coupon").strip() or None

    if None in (required_qty, discounted_qty, discount_percent, valid_from, valid_to):
        print("Coupon ignored (missing fields).")
        return

    coupon = teller.create_coupon(
        product,
        required_qty=required_qty,
        discounted_qty=discounted_qty,
        discount_percent=discount_percent,
        valid_from=valid_from,
        valid_to=valid_to,
        description=description or "coupon",
    )
    teller.use_coupon(coupon)
    print("Coupon set for this checkout.")


def configure_loyalty():
    if not yes_no("Use loyalty points? (y/n)", "y"):
        return None, 0

    current_points = int(prompt_with_default("Current points balance (integer, 1 point = 1 cent):", "200") or "0")
    points_to_redeem = int(prompt_with_default("Points to redeem now (integer):", "150") or "0")
    return LoyaltyAccount(points=current_points), points_to_redeem


def main():
    catalog = FakeCatalog()
    read_catalog(Path("catalog.csv"), catalog)
    if not catalog.products:
        print("No catalog found. Create a 'catalog.csv' in this folder first (columns: name, unit, price).")
        return

    teller = Teller(catalog)
    read_offers(Path("offers.csv"), teller, catalog)

    configure_bundle_offers(teller, catalog)
    configure_coupon(teller, catalog)

    cart = build_cart(catalog)
    checkout_date = parse_date("Checkout date (YYYY-MM-DD, empty = today):", "2025-12-14") or date.today()
    loyalty_account, points_to_redeem = configure_loyalty()

    receipt = teller.checks_out_articles_from(
        cart,
        checkout_date=checkout_date,
        loyalty_account=loyalty_account,
        points_to_redeem=points_to_redeem,
    )

    print()
    print(ReceiptPrinter().print_receipt(receipt))
    if loyalty_account:
        print(f"Points earned: {receipt.points_earned}")
        print(f"Points redeemed: {receipt.points_redeemed}")
        print(f"New balance: {loyalty_account.points}")


if __name__ == "__main__":
    main()
