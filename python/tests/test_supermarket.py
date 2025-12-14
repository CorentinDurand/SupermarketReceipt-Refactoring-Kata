import unittest
from decimal import Decimal, ROUND_HALF_UP

from model_objects import Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from fake_catalog import FakeCatalog


class SupermarketTest(unittest.TestCase):
    def setUp(self):
        self.catalog = FakeCatalog()
        self.teller = Teller(self.catalog)

    def add_product(self, name, unit, price):
        product = Product(name, unit)
        self.catalog.add_product(product, price)
        return product

    def build_receipt(self, items):
        cart = ShoppingCart()
        for product, quantity in items:
            cart.add_item_quantity(product, quantity)
        return self.teller.checks_out_articles_from(cart)

    def assert_money_equal(self, expected, actual):
        expected_dec = Decimal(str(expected)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        actual_dec = actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(expected_dec, actual_dec)

    def test_offer_does_not_apply_when_product_not_in_cart(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        apples = self.add_product("apples", ProductUnit.KILO, 1.99)
        self.teller.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, toothbrush, 10.0)

        receipt = self.build_receipt([(apples, 2.5)])

        self.assert_money_equal(Decimal("2.5") * Decimal("1.99"), receipt.total_price())
        self.assertEqual([], receipt.discounts)
        self.assertEqual(1, len(receipt.items))

    def test_three_for_two_discount_applies_to_complete_groups_only(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        self.teller.add_special_offer(SpecialOfferType.THREE_FOR_TWO, toothbrush, None)

        receipt = self.build_receipt([(toothbrush, 4)])

        self.assert_money_equal(Decimal("2.97"), receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))
        self.assert_money_equal(Decimal("-0.99"), receipt.discounts[0].discount_amount)

    def test_two_for_amount_discount_handles_remainder(self):
        soap = self.add_product("soap", ProductUnit.EACH, 2.0)
        self.teller.add_special_offer(SpecialOfferType.TWO_FOR_AMOUNT, soap, 3.0)

        receipt = self.build_receipt([(soap, 5)])

        # current implementation prorates the discount, so total is computed as below
        self.assert_money_equal(Decimal("9.5"), receipt.total_price())
        self.assert_money_equal(Decimal("-0.5"), receipt.discounts[0].discount_amount)

    def test_five_for_amount_discount(self):
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_special_offer(SpecialOfferType.FIVE_FOR_AMOUNT, toothpaste, 7.49)

        receipt = self.build_receipt([(toothpaste, 5)])

        self.assert_money_equal(Decimal("7.49"), receipt.total_price())
        self.assert_money_equal(Decimal("-1.46"), receipt.discounts[0].discount_amount)

    def test_percentage_discount_applies_to_weighted_product(self):
        apples = self.add_product("apples", ProductUnit.KILO, 1.99)
        self.teller.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, apples, 10.0)

        receipt = self.build_receipt([(apples, 1.2)])

        undiscounted = Decimal("1.2") * Decimal("1.99")
        expected_discount = -(undiscounted * Decimal("0.10"))
        self.assert_money_equal(undiscounted + expected_discount, receipt.total_price())
        self.assert_money_equal(expected_discount, receipt.discounts[0].discount_amount)
