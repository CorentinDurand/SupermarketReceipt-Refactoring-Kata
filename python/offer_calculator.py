from decimal import Decimal

from discount_strategies import (
    BundleStrategy,
    CouponStrategy,
    NForAmountStrategy,
    PercentDiscountStrategy,
    ThreeForTwoStrategy,
)
from model_objects import SpecialOfferType


class OfferCalculator:

    def __init__(self):
        self._regular_strategies = {
            SpecialOfferType.THREE_FOR_TWO: ThreeForTwoStrategy(),
            SpecialOfferType.TEN_PERCENT_DISCOUNT: PercentDiscountStrategy(),
            SpecialOfferType.TWO_FOR_AMOUNT: NForAmountStrategy(2),
            SpecialOfferType.FIVE_FOR_AMOUNT: NForAmountStrategy(5),
        }
        self._bundle_strategy = BundleStrategy()
        self._coupon_strategy = CouponStrategy()

    def calculate_discount(self, offer, product, quantity, unit_price):
        strategy = self._regular_strategies.get(offer.offer_type)
        if not strategy:
            return None
        return strategy.calculate(offer, product, quantity, unit_price)

    def calculate_discount_for_quantity(self, offer, product, quantity, unit_price):
        return self.calculate_discount(offer, product, quantity, unit_price)

    def count_complete_bundles(self, bundle_offer, quantities):
        return self._bundle_strategy.count_complete_bundles(bundle_offer, quantities)

    def best_bundle_discount(self, bundle_offer, bundle_count, quantities, offers, catalog):
        return self._bundle_strategy.best_bundle_discount(bundle_offer, bundle_count, quantities, offers, catalog, self)

    def consume_bundle_quantities(self, bundle_offer, bundle_count, quantities):
        self._bundle_strategy.consume_bundle_quantities(bundle_offer, bundle_count, quantities)

    def apply_coupon(self, coupon, quantities, catalog, checkout_date):
        result = self.compute_coupon_discount(coupon, quantities, catalog, checkout_date)
        if not result:
            return None
        discount, consumed = result
        coupon.redeemed = True
        return discount, consumed

    def compute_coupon_discount(self, coupon, quantities, catalog, checkout_date):
        return self._coupon_strategy.compute_discount(coupon, quantities, catalog, checkout_date)
