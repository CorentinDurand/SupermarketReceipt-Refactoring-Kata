import unittest
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from model_objects import LoyaltyAccount, Product, ProductUnit
from shopping_cart import ShoppingCart
from teller import Teller
from fake_catalog import FakeCatalog


class LoyaltyProgramTest(unittest.TestCase):
    def setUp(self):
        self.catalog = FakeCatalog()
        self.teller = Teller(self.catalog)

    def assert_money_equal(self, expected, actual):
        expected_dec = Decimal(str(expected)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        actual_dec = actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(expected_dec, actual_dec)

    def test_earns_points_from_amount_paid(self):
        milk = Product("milk", ProductUnit.EACH)
        self.catalog.add_product(milk, 1.50)
        account = LoyaltyAccount()

        cart = ShoppingCart()
        cart.add_item_quantity(milk, 2)

        receipt = self.teller.checks_out_articles_from(cart, checkout_date=date(2025, 11, 14), loyalty_account=account)

        self.assert_money_equal(Decimal("3.00"), receipt.total_price())
        self.assertEqual(300, receipt.points_earned)
        self.assertEqual(300, account.points)

    def test_can_redeem_points_as_payment(self):
        toothbrush = Product("toothbrush", ProductUnit.EACH)
        self.catalog.add_product(toothbrush, 0.99)
        account = LoyaltyAccount(points=200)  # 2.00

        cart = ShoppingCart()
        cart.add_item_quantity(toothbrush, 3)  # 2.97 total

        receipt = self.teller.checks_out_articles_from(
            cart,
            checkout_date=date(2025, 11, 14),
            loyalty_account=account,
            points_to_redeem=150,  # 1.50
        )

        self.assert_money_equal(Decimal("2.97") - Decimal("1.50"), receipt.total_price())
        self.assertEqual(150, receipt.points_redeemed)
        # Earned points are based on the amount actually paid after redeeming points.
        expected_paid_points = int((receipt.total_price() * Decimal("100")).to_integral_value())
        self.assertEqual(200 - 150 + expected_paid_points, account.points)
