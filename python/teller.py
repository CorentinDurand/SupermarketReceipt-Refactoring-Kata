from decimal import Decimal, ROUND_FLOOR
from datetime import date

from model_objects import Offer, BundleOffer, Coupon
from receipt import Receipt


class Teller:

    def __init__(self, catalog):
        self.catalog = catalog
        self.offers = {}
        self.bundle_offers = []
        self.coupon = None

    def add_special_offer(self, offer_type, product, argument):
        self.offers[product] = Offer(offer_type, product, argument)

    def add_bundle_offer(self, items_required, discount_percent=10):
        self.bundle_offers.append(BundleOffer(items_required, discount_percent))

    def create_coupon(self, product, required_qty, discounted_qty, discount_percent, valid_from, valid_to, description=None):
        return Coupon(product, required_qty, discounted_qty, discount_percent, valid_from, valid_to, description)

    def use_coupon(self, coupon):
        self.coupon = coupon

    def checks_out_articles_from(self, the_cart, checkout_date=None, loyalty_account=None, points_to_redeem=0):
        checkout_date = checkout_date or date.today()
        receipt = Receipt()
        product_quantities = the_cart.items
        for pq in product_quantities:
            p = pq.product
            quantity = pq.quantity
            unit_price = self.catalog.unit_price(p)
            price = unit_price * Decimal(str(quantity))
            receipt.add_product(p, quantity, unit_price, price)

        the_cart.handle_offers(receipt, self.offers, self.bundle_offers, self.coupon, self.catalog, checkout_date)

        self._apply_loyalty(loyalty_account, receipt, points_to_redeem)
        return receipt

    def _apply_loyalty(self, loyalty_account, receipt, points_to_redeem):
        if not loyalty_account:
            return

        points_to_redeem = int(points_to_redeem or 0)
        if points_to_redeem < 0:
            raise ValueError("points_to_redeem must be >= 0")

        total_due = receipt.total_price()
        max_points_for_due = int((total_due * 100).to_integral_value(rounding=ROUND_FLOOR))
        points_redeemed = min(points_to_redeem, max_points_for_due, loyalty_account.points)
        if points_redeemed:
            loyalty_account.redeem(points_redeemed)
            value = (Decimal(points_redeemed) / Decimal("100"))
            receipt.add_payment("Loyalty points", -value)
            receipt.points_redeemed = points_redeemed

        total_paid = receipt.total_price()
        points_earned = int((total_paid * 100).to_integral_value(rounding=ROUND_FLOOR))
        loyalty_account.earn(points_earned)
        receipt.points_earned = points_earned
