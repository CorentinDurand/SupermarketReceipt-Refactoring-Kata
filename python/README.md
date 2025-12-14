# Supermarket Receipt in [Python](https://www.python.org/)

## Setup

* Have Python installed
* Clone the repository
* On the command line, enter the `SupermarketReceipt-Refactoring-Kata/python` directory
* On the command line, install requirements, e.g. on the`python -m pip install -r requirements.txt`

## Running Tests

On the command line, enter the `SupermarketReceipt-Refactoring-Kata/python` directory and run

```
python -m unittest
```

## Optional: Running the Interactive Demo

On the command line, enter the `SupermarketReceipt-Refactoring-Kata/python` directory and run

```
python scripts/interactive_checkout.py
```

This script lets you choose your cart and see the receipt with offers/bundles/coupons/loyalty applied.

If present, `scripts/interactive_checkout.py` also loads from `data/`:
- `data/bundles.csv` (optional, predefined bundles)
- `data/coupons.csv` (optional, predefined coupons)
- `data/cart.csv` (optional, predefined cart)

## Week 1 - Additional Discount Test Coverage

Before refactoring the discount engine, a dedicated `tests/test_supermarket.py` suite was added to pin down the current behaviour of every existing offer type:

1. `test_offer_does_not_apply_when_product_not_in_cart` – ensures no discount is emitted unless the qualifying product is actually purchased.
2. `test_three_for_two_discount_applies_to_complete_groups_only` – validates the “3 for 2” creator issues one discount per complete trio.
3. `test_two_for_amount_discount_handles_remainder` – documents today's prorated discount for “2 for amount”, guarding current behaviour until it is fixed.
4. `test_five_for_amount_discount` – covers the “5 for amount” multi-buy logic so future changes don’t break it inadvertently.
5. `test_percentage_discount_applies_to_weighted_product` – checks percentage-based offers on weighted goods (e.g., apples by the kilo).

Together these tests provide confidence that the discount creation logic keeps functioning while we clean up or extend the codebase (bundles, coupons, loyalty, etc.). Run them with `python -m unittest` from this directory.

## Week 2 - Code Smell Detection and Fixes

SonarQube highlighted the main smells in the Python module and how they were addressed:
- `shopping_cart.py`: reduced cognitive complexity in `handle_offers` by delegating to an offer calculator.
- `catalog.py`: replaced generic `Exception` with `NotImplementedError` to signal abstract methods.
- `receipt_printer.py`: unused loop index switched to `_` to make intent explicit.

## Week 3 - Foundational Refactors for New Features

To prepare for bundles, coupons, and loyalty while keeping money handling precise:
- Introduced `offer_calculator.py` to encapsulate discount formulas and keep `ShoppingCart` focused on orchestration.
- Switched currency amounts to `Decimal` (prices, discounts, receipt totals) to avoid floating-point rounding issues; conversion happens only when printing the receipt.
- Added value-based equality/hash on `Product` to make catalog and offer lookups robust.
- Moved the in-memory `FakeCatalog` out of `tests/` and extracted CSV parsing into `csv_loaders.py` to keep the interactive demo clean.
- Confirmed all existing tests still pass to lock current behaviour before adding new feature code.

## Week 3, 4, 5 - Develop new features, starting from refactoring the existing solution

### Bundles (Discounted Packs)

- Added `SpecialOfferType.BUNDLE` and `BundleOffer` (10% off per complete bundle, e.g., toothbrush + toothpaste).
- `Teller.add_bundle_offer` registers bundles; `OfferCalculator` counts complete bundles and compares the bundle gain to any competing per-product offers on the same items, applying only the best option.
- Quantities consumed by a bundle are removed from subsequent offer calculations; the checkout simulates alternatives (bundle vs coupon vs per-product offers) and applies the cheapest result.
- New tests cover complete bundles, incomplete bundles (no discount), multiple bundles, partial excess (one bundle applied, extras at full price), and prioritizing a better per-product offer over the bundle (e.g., toothpaste “5 for 7.49” beats the bundle when it’s cheaper overall).

### Coupons (Date- and Quantity-Limited Discounts)

- Added `Coupon` support: one-time use, valid within a date range, with required and discounted quantities (e.g., buy 6 juices, get up to 6 more at 50%).
- `Teller.create_coupon` builds a coupon and `Teller.use_coupon` activates it for checkout; `OfferCalculator` applies it only if the checkout date is within range and enough quantity is present, and then marks it redeemed.
- Coupon-consumed quantities are removed from further offers to avoid stacking; if the coupon is expired or insufficient quantity is present, it is ignored.
- Coupons are also considered in the global “best discount” selection when they overlap with bundles or other offers.
- New tests cover valid coupon application and expiry outside the valid window.

### Loyalty Program (Credit Points)

- Added `LoyaltyAccount` (integer points) that can be used as a supplementary payment method: `points_to_redeem` reduces the total due (1 point = 1 cent).
- Points are redeemed up to the amount due and the available balance; points are earned from the amount actually paid after discounts and point redemption.
- Receipt now tracks `points_earned` and `points_redeemed`, and prints a “Loyalty points” payment line when points are used.
- New tests cover earning points and redeeming points on a purchase.

## Interactive Demo (Choose Your Cart)

To build a cart manually and print a receipt with offers/bundles/coupons/loyalty applied, run from `SupermarketReceipt-Refactoring-Kata/python`:
```
python scripts/interactive_checkout.py
```

This script uses `data/catalog.csv` (required) and `data/offers.csv` (optional), then prompts you to add bundles, coupons, cart items, and loyalty points.
You can press Enter to accept the suggested defaults (typical demo scenario).

Example files are provided:
- `data/catalog.csv` (products + units + prices)
- `data/offers.csv` (classic special offers)
