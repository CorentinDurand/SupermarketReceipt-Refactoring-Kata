
from decimal import Decimal

class ReceiptItem:
    def __init__(self, product, quantity, price, total_price):
        self.product = product
        self.quantity = quantity
        self.price = price
        self.total_price = total_price


class Payment:
    def __init__(self, description, amount):
        self.description = description
        self.amount = amount


class Receipt:
    def __init__(self):
        self._items = []
        self._discounts = []
        self._payments = []
        self.points_earned = 0
        self.points_redeemed = 0

    def total_price(self):
        total = Decimal("0")
        for item in self.items:
            total += item.total_price
        for discount in self.discounts:
            total += discount.amount
        for payment in self.payments:
            total += payment.amount
        return total

    def add_product(self, product, quantity, price, total_price):
        self._items.append(ReceiptItem(product, quantity, price, total_price))

    def add_discount(self, discount):
        self._discounts.append(discount)

    def add_payment(self, description, amount):
        self._payments.append(Payment(description, amount))

    @property
    def items(self):
        return self._items[:]

    @property
    def discounts(self):
        return self._discounts[:]

    @property
    def payments(self):
        return self._payments[:]
