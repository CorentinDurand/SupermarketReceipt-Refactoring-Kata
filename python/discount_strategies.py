from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from model_objects import Discount, SpecialOfferType


class DiscountStrategy:
    def calculate(self, offer, product, quantity, unit_price):
        raise NotImplementedError


class ThreeForTwoStrategy(DiscountStrategy):
    def calculate(self, offer, product, quantity, unit_price):
        quantity_dec = Decimal(str(quantity))
        quantity_as_int = int(quantity_dec)
        if quantity_as_int <= 2:
            return None

        trios = quantity_as_int // 3
        discount_amount = quantity_dec * unit_price - (
            (Decimal(trios) * Decimal(2) * unit_price) + Decimal(quantity_as_int % 3) * unit_price
        )
        return Discount(product, "3 for 2", -discount_amount)


class PercentDiscountStrategy(DiscountStrategy):
    def calculate(self, offer, product, quantity, unit_price):
        quantity_dec = Decimal(str(quantity))
        percent = Decimal(str(offer.argument))
        return Discount(product, f"{percent}% off", -(quantity_dec * unit_price * percent / Decimal("100")))


@dataclass(frozen=True)
class NForAmountStrategy(DiscountStrategy):
    group_size: int

    def calculate(self, offer, product, quantity, unit_price):
        quantity_dec = Decimal(str(quantity))
        quantity_as_int = int(quantity_dec)
        if quantity_as_int < self.group_size:
            return None

        offer_amount_dec = Decimal(str(offer.argument))
        total = offer_amount_dec * (Decimal(quantity_as_int) / Decimal(self.group_size)) + Decimal(
            quantity_as_int % self.group_size
        ) * unit_price
        discount_amount = (unit_price * quantity_dec) - total
        return Discount(product, f"{self.group_size} for {offer_amount_dec}", -discount_amount)


class BundleStrategy:
    def count_complete_bundles(self, bundle_offer, quantities):
        if not bundle_offer.items_required:
            return 0
        counts = []
        for product, required_qty in bundle_offer.items_required.items():
            available = quantities.get(product, Decimal("0"))
            counts.append(int(available // required_qty))
        return min(counts) if counts else 0

    def consume_bundle_quantities(self, bundle_offer, bundle_count, quantities):
        for product, required_qty in bundle_offer.items_required.items():
            if product in quantities:
                quantities[product] -= required_qty * Decimal(bundle_count)
                if quantities[product] <= 0:
                    quantities.pop(product)

    def best_bundle_discount(self, bundle_offer, bundle_count, quantities, offers, catalog, offer_calculator):
        bundle_total = Decimal("0")
        for product, required_qty in bundle_offer.items_required.items():
            unit_price = catalog.unit_price(product)
            bundle_total += unit_price * required_qty

        bundle_discount_amount = bundle_total * bundle_offer.discount_percent / Decimal("100")
        bundle_discount_amount *= Decimal(bundle_count)

        alternative_discount = Decimal("0")
        for product, _required_qty in bundle_offer.items_required.items():
            offer = offers.get(product)
            if not offer:
                continue
            unit_price = catalog.unit_price(product)
            available_qty = quantities.get(product, Decimal("0"))
            alt = offer_calculator.calculate_discount_for_quantity(offer, product, available_qty, unit_price)
            if alt:
                alternative_discount += alt.amount

        if bundle_discount_amount >= abs(alternative_discount):
            description = f"bundle {bundle_offer.discount_percent}% off"
            first_product = next(iter(bundle_offer.items_required.keys()))
            return Discount(first_product, description, -bundle_discount_amount), True
        return None, False


class CouponStrategy:
    def compute_discount(self, coupon, quantities, catalog, checkout_date):
        if not coupon or not coupon.is_valid_on(checkout_date):
            return None

        product = coupon.product
        available = quantities.get(product, Decimal("0"))
        if available <= coupon.required_qty:
            return None

        unit_price = catalog.unit_price(product)
        discounted_qty = min(available - coupon.required_qty, coupon.discounted_qty)
        if discounted_qty <= 0:
            return None

        discount_amount = unit_price * discounted_qty * coupon.discount_percent / Decimal("100")
        description = f"{coupon.description} {coupon.discount_percent}% off"
        consumed = {product: coupon.required_qty + discounted_qty}
        return Discount(product, description, -discount_amount), consumed
