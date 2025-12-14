import unittest
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from model_objects import Product, ProductUnit
from shopping_cart import ShoppingCart
from teller import Teller
from fake_catalog import FakeCatalog


class CouponTest(unittest.TestCase):
    def setUp(self):
        self.catalog = FakeCatalog()
        self.teller = Teller(self.catalog)

    def add_product(self, name, unit, price):
        product = Product(name, unit)
        self.catalog.add_product(product, price)
        return product

    def checkout_with_date(self, items, checkout_date):
        cart = ShoppingCart()
        for product, quantity in items:
            cart.add_item_quantity(product, quantity)
        return self.teller.checks_out_articles_from(cart, checkout_date=checkout_date)

    def assert_money_equal(self, expected, actual):
        expected_dec = Decimal(str(expected)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        actual_dec = actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(expected_dec, actual_dec)

    def test_coupon_applies_within_valid_dates(self):
        juice = self.add_product("orange juice", ProductUnit.EACH, 1.50)
        valid_from = date(2025, 11, 13)
        valid_to = date(2025, 11, 15)
        coupon = self.teller.create_coupon(
            juice,
            required_qty=6,
            discounted_qty=6,
            discount_percent=50,
            valid_from=valid_from,
            valid_to=valid_to,
            description="orange juice coupon",
        )
        self.teller.use_coupon(coupon)

        receipt = self.checkout_with_date([(juice, 12)], checkout_date=date(2025, 11, 14))

        expected_discount = -(Decimal("1.50") * Decimal("6") * Decimal("0.5"))
        expected_total = Decimal("12") * Decimal("1.50") + expected_discount
        self.assert_money_equal(expected_total, receipt.total_price())
        self.assert_money_equal(expected_discount, receipt.discounts[0].discount_amount)

    def test_coupon_not_applied_if_expired(self):
        juice = self.add_product("orange juice", ProductUnit.EACH, 1.50)
        valid_from = date(2025, 11, 13)
        valid_to = date(2025, 11, 15)
        coupon = self.teller.create_coupon(
            juice,
            required_qty=6,
            discounted_qty=6,
            discount_percent=50,
            valid_from=valid_from,
            valid_to=valid_to,
            description="orange juice coupon",
        )
        self.teller.use_coupon(coupon)

        receipt = self.checkout_with_date([(juice, 12)], checkout_date=date(2025, 11, 16))

        self.assertEqual([], receipt.discounts)
        self.assert_money_equal(Decimal("12") * Decimal("1.50"), receipt.total_price())

    def test_choose_coupon_over_bundle_when_coupon_saves_more(self):
        juice = self.add_product("orange juice", ProductUnit.EACH, 1.50)
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        self.teller.add_bundle_offer({juice: 1, toothbrush: 1})  # 10% off (1 juice + 1 toothbrush)

        valid_from = date(2025, 11, 13)
        valid_to = date(2025, 11, 15)
        coupon = self.teller.create_coupon(
            juice,
            required_qty=6,
            discounted_qty=6,
            discount_percent=50,
            valid_from=valid_from,
            valid_to=valid_to,
            description="orange juice coupon",
        )
        self.teller.use_coupon(coupon)

        receipt = self.checkout_with_date([(juice, 12), (toothbrush, 1)], checkout_date=date(2025, 11, 14))

        expected_total = (Decimal("12") * Decimal("1.50") + Decimal("0.99")) - (Decimal("6") * Decimal("1.50") * Decimal("0.5"))
        self.assert_money_equal(expected_total, receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))
        self.assertIn("orange juice coupon", receipt.discounts[0].description)
