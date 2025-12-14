import unittest
from decimal import Decimal, ROUND_HALF_UP

from model_objects import Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from fake_catalog import FakeCatalog


class BundleOfferTest(unittest.TestCase):
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

    def test_bundle_applies_for_complete_set(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_bundle_offer({toothbrush: 1, toothpaste: 1})

        receipt = self.build_receipt([(toothbrush, 1), (toothpaste, 1)])

        expected_total = (Decimal("0.99") + Decimal("1.79")) * Decimal("0.9")
        self.assert_money_equal(expected_total, receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))

    def test_incomplete_bundle_gets_no_discount(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_bundle_offer({toothbrush: 1, toothpaste: 1})

        receipt = self.build_receipt([(toothbrush, 2)])

        self.assert_money_equal(Decimal("0.99") * Decimal("2"), receipt.total_price())
        self.assertEqual([], receipt.discounts)

    def test_multiple_bundles_apply_per_complete_set(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_bundle_offer({toothbrush: 1, toothpaste: 1})

        receipt = self.build_receipt([(toothbrush, 2), (toothpaste, 2)])

        expected_total = (Decimal("0.99") + Decimal("1.79")) * Decimal("2") * Decimal("0.9")
        self.assert_money_equal(expected_total, receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))

    def test_only_one_bundle_applied_when_extra_items_left(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_bundle_offer({toothbrush: 1, toothpaste: 1})

        receipt = self.build_receipt([(toothbrush, 2), (toothpaste, 1)])

        bundle_total = (Decimal("0.99") + Decimal("1.79")) * Decimal("0.9")
        remaining = Decimal("0.99")
        expected_total = bundle_total + remaining

        self.assert_money_equal(expected_total, receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))

    def test_choose_better_per_product_offer_over_bundle(self):
        toothbrush = self.add_product("toothbrush", ProductUnit.EACH, 0.99)
        toothpaste = self.add_product("toothpaste", ProductUnit.EACH, 1.79)
        self.teller.add_bundle_offer({toothbrush: 1, toothpaste: 1})
        self.teller.add_special_offer(SpecialOfferType.FIVE_FOR_AMOUNT, toothpaste, 7.49)

        receipt = self.build_receipt([(toothpaste, 5), (toothbrush, 1)])

        # Best outcome should use the toothpaste offer (5 for 7.49) and leave the bundle aside.
        expected_total = Decimal("7.49") + Decimal("0.99")
        self.assert_money_equal(expected_total, receipt.total_price())
        self.assertEqual(1, len(receipt.discounts))
