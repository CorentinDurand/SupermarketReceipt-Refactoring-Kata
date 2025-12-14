from decimal import Decimal
from enum import Enum


class Product:
    def __init__(self, name, unit):
        self.name = name
        self.unit = unit

    def __eq__(self, other):
        return isinstance(other, Product) and self.name == other.name and self.unit == other.unit

    def __hash__(self):
        return hash((self.name, self.unit))


class ProductQuantity:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity


class ProductUnit(Enum):
    EACH = 1
    KILO = 2


class SpecialOfferType(Enum):
    THREE_FOR_TWO = 1
    TEN_PERCENT_DISCOUNT = 2
    TWO_FOR_AMOUNT = 3
    FIVE_FOR_AMOUNT = 4
    BUNDLE = 5
    COUPON = 6

class Offer:
    def __init__(self, offer_type, product, argument):
        self.offer_type = offer_type
        self.product = product
        self.argument = argument


class Discount:
    def __init__(self, product, description, discount_amount):
        self.product = product
        self.description = description
        self.amount = Decimal(str(discount_amount))

    @property
    def discount_amount(self):
        return self.amount


class BundleOffer:
    def __init__(self, items_required, discount_percent=10):
        self.items_required = {product: Decimal(str(qty)) for product, qty in items_required.items()}
        self.discount_percent = Decimal(str(discount_percent))


class Coupon:
    def __init__(self, product, required_qty, discounted_qty, discount_percent, valid_from, valid_to, description=None):
        self.product = product
        self.required_qty = Decimal(str(required_qty))
        self.discounted_qty = Decimal(str(discounted_qty))
        self.discount_percent = Decimal(str(discount_percent))
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.description = description or "coupon"
        self.redeemed = False

    def is_valid_on(self, date):
        return (self.valid_from <= date <= self.valid_to) and not self.redeemed


class LoyaltyAccount:
    def __init__(self, points=0):
        self.points = int(points)

    def redeem(self, points):
        points = int(points)
        if points < 0:
            raise ValueError("points must be >= 0")
        if points > self.points:
            raise ValueError("insufficient points")
        self.points -= points
        return points

    def earn(self, points):
        points = int(points)
        if points < 0:
            raise ValueError("points must be >= 0")
        self.points += points
        return points
