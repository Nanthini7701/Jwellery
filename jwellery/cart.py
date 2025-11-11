# jwellery/cart.py
from decimal import Decimal
from django.conf import settings
from jwellery.models import Product

CART_SESSION_ID = getattr(settings, "CART_SESSION_ID", "cart")

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        We store price as string (to be JSON serializable in session).
        """
        pid = str(product.id)
        price_str = str(product.price)  # ensure string to save in session

        item = self.cart.get(pid)
        if not item:
            self.cart[pid] = {"quantity": 0, "price": price_str}
            item = self.cart[pid]

        if override_quantity:
            item["quantity"] = quantity
        else:
            item["quantity"] = item.get("quantity", 0) + quantity

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart, attach the Product instance,
        and compute total_price. Be defensive: if 'price' missing, use product.price.
        """
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)

        # Map products by id for fast lookup
        products_map = {str(p.id): p for p in products}

        for pid in product_ids:
            item = self.cart[pid].copy()  # work on a copy to avoid mutating session directly
            product = products_map.get(pid)

            # If product doesn't exist in DB, skip or you could remove it
            if not product:
                # optional: remove stale item from session
                # del self.cart[pid]; self.save()
                continue

            # Price: prefer stored price, else use live product price
            price_value = item.get("price")
            if price_value is None or price_value == "":
                price_value = str(product.price)

            # Convert to Decimal for arithmetic
            item["price"] = Decimal(price_value)
            item["quantity"] = int(item.get("quantity", 0))
            item["product"] = product
            item["total_price"] = item["price"] * item["quantity"]

            yield item

    def __len__(self):
        """Return total quantity of items in the cart."""
        return sum(int(item.get("quantity", 0)) for item in self.cart.values())

    def get_total_price(self):
        total = Decimal("0.00")
        for pid in list(self.cart.keys()):
            item = self.cart[pid]
            price_value = item.get("price")
            # if missing, fallback to DB price
            if not price_value:
                try:
                    product = Product.objects.get(id=pid)
                    price_value = str(product.price)
                except Product.DoesNotExist:
                    price_value = "0.00"
            total += Decimal(price_value) * int(item.get("quantity", 0))
        return total

    def clear(self):
        """Remove cart from session."""
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
            self.save()
