from decimal import Decimal
from model_objects import ProductQuantity
from offer_calculator import OfferCalculator


class ShoppingCart:

    def __init__(self):
        self._items = []
        self._product_quantities = {}
        self._offer_calculator = OfferCalculator()

    @property
    def items(self):
        return self._items

    def add_item(self, product):
        self.add_item_quantity(product, 1.0)

    @property
    def product_quantities(self):
        return self._product_quantities

    def add_item_quantity(self, product, quantity):
        quantity_dec = Decimal(str(quantity))
        self._items.append(ProductQuantity(product, quantity_dec))
        if product in self._product_quantities:
            self._product_quantities[product] = self._product_quantities[product] + quantity_dec
        else:
            self._product_quantities[product] = quantity_dec

    def handle_offers(self, receipt, offers, bundle_offers, coupon, catalog, checkout_date):
        best = self._select_best_discount_plan(offers, bundle_offers, coupon, catalog, checkout_date)
        for discount in best:
            receipt.add_discount(discount)

    def _select_best_discount_plan(self, offers, bundle_offers, coupon, catalog, checkout_date):
        base_quantities = dict(self._product_quantities)

        plans = [
            self._compute_plan_no_coupon(base_quantities, offers, bundle_offers, catalog),
        ]

        if coupon and coupon.is_valid_on(checkout_date):
            # Evaluate coupon before bundles/offers and also after bundles (both can be optimal depending on quantities).
            plans.append(
                self._compute_plan_coupon_first(base_quantities, offers, bundle_offers, coupon, catalog, checkout_date)
            )
            plans.append(
                self._compute_plan_coupon_after_bundles(base_quantities, offers, bundle_offers, coupon, catalog, checkout_date)
            )

        # Choose the plan with the largest savings (most negative sum of discount amounts).
        best_discounts, best_savings, uses_coupon = max(plans, key=lambda p: p[1])
        if coupon and uses_coupon:
            coupon.redeemed = True
        return best_discounts

    def _compute_plan_no_coupon(self, quantities, offers, bundle_offers, catalog):
        remaining = dict(quantities)
        discounts = []

        discounts.extend(self._apply_bundles(remaining, offers, bundle_offers, catalog))
        discounts.extend(self._apply_regular_offers(remaining, offers, catalog))

        savings = self._savings_from_discounts(discounts)
        return discounts, savings, False

    def _compute_plan_coupon_first(self, quantities, offers, bundle_offers, coupon, catalog, checkout_date):
        remaining = dict(quantities)
        discounts = []
        uses_coupon = False

        coupon_discount = self._offer_calculator.compute_coupon_discount(coupon, remaining, catalog, checkout_date)
        if coupon_discount:
            discount, consumed = coupon_discount
            discounts.append(discount)
            self._consume(consumed, remaining)
            uses_coupon = True

        discounts.extend(self._apply_bundles(remaining, offers, bundle_offers, catalog))
        discounts.extend(self._apply_regular_offers(remaining, offers, catalog))

        savings = self._savings_from_discounts(discounts)
        return discounts, savings, uses_coupon

    def _compute_plan_coupon_after_bundles(self, quantities, offers, bundle_offers, coupon, catalog, checkout_date):
        remaining = dict(quantities)
        discounts = []
        uses_coupon = False

        discounts.extend(self._apply_bundles(remaining, offers, bundle_offers, catalog))

        coupon_discount = self._offer_calculator.compute_coupon_discount(coupon, remaining, catalog, checkout_date)
        if coupon_discount:
            discount, consumed = coupon_discount
            discounts.append(discount)
            self._consume(consumed, remaining)
            uses_coupon = True

        discounts.extend(self._apply_regular_offers(remaining, offers, catalog))

        savings = self._savings_from_discounts(discounts)
        return discounts, savings, uses_coupon

    def _apply_bundles(self, remaining_quantities, offers, bundle_offers, catalog):
        discounts = []
        for bundle_offer in bundle_offers:
            bundle_count = self._offer_calculator.count_complete_bundles(bundle_offer, remaining_quantities)
            if bundle_count == 0:
                continue

            bundle_discount, applied = self._offer_calculator.best_bundle_discount(
                bundle_offer, bundle_count, remaining_quantities, offers, catalog
            )
            if applied:
                discounts.append(bundle_discount)
                self._offer_calculator.consume_bundle_quantities(bundle_offer, bundle_count, remaining_quantities)
        return discounts

    def _apply_regular_offers(self, remaining_quantities, offers, catalog):
        discounts = []
        for product, quantity in list(remaining_quantities.items()):
            offer = offers.get(product)
            if not offer:
                continue
            unit_price = catalog.unit_price(product)
            discount = self._offer_calculator.calculate_discount(offer, product, quantity, unit_price)
            if discount:
                discounts.append(discount)
        return discounts

    def _consume(self, consumed, remaining_quantities):
        for product, qty in consumed.items():
            if product in remaining_quantities:
                remaining_quantities[product] -= qty
                if remaining_quantities[product] <= 0:
                    remaining_quantities.pop(product)

    def _savings_from_discounts(self, discounts):
        # Savings is the positive amount saved.
        total = Decimal("0")
        for d in discounts:
            total += (-d.amount)
        return total
