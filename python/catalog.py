
class SupermarketCatalog:

    def add_product(self, product, price):
        raise NotImplementedError("cannot be called from a unit test - it accesses the database")

    def unit_price(self, product):
        raise NotImplementedError("cannot be called from a unit test - it accesses the database")

