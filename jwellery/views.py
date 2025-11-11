import razorpay
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
# adjust imports to your app
from django.contrib import messages
from django.http import Http404
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm, OrderCreateForm
from .models import Product, Category, Order, OrderItem, Wishlist
from .cart import Cart

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Home View
def home(request):
    categories = Category.objects.all()
    cart = Cart(request)
    return render(request, 'jwellery/home.html', {'categories': categories, 'cart': cart})

# About View
def about_view(request):
    categories = Category.objects.all()
    cart = Cart(request)
    return render(request, 'jwellery/about.html', {'categories': categories, 'cart': cart})

# Signup View
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('jwellery:product_list')
    else:
        form = SignUpForm()
    cart = Cart(request)
    return render(request, 'jwellery/signup.html', {'form': form, 'cart': cart})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('jwellery:product_list')
    else:
        form = AuthenticationForm()
    cart = Cart(request)
    return render(request, 'jwellery/login.html', {'form': form, 'cart': cart})

# Logout View
def logout_view(request):
    logout(request)
    return redirect('jwellery:home')

# Product List
def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    cart = Cart(request)
    return render(request, 'jwellery/product_list.html', {'categories': categories, 'products': products, 'cart': cart})

# Product Detail
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    categories = Category.objects.all()
    cart = Cart(request)
    return render(request, 'jwellery/product_detail.html', {'product': product, 'categories': categories, 'cart': cart})

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)

    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'jwellery/category_products.html', context)
# Cart Add
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = request.session.get(settings.CART_SESSION_ID, {})
    # simple add 1 quantity (adjust to your cart model)
    cart_item = cart.get(str(product_id), {"quantity": 0})
    cart_item["quantity"] = cart_item.get("quantity", 0) + 1
    cart[str(product_id)] = cart_item
    request.session[settings.CART_SESSION_ID] = cart
    return redirect("jwellery:cart_detail")
# Cart Remove
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect(request.META.get('HTTP_REFERER', 'jwellery:cart_detail'))

# Cart Detail
def cart_detail(request):
    cart = Cart(request)
    # optional: categories for header dropdown
    categories = Category.objects.all()
    return render(request, 'jwellery/cart_detail.html', {
        'cart': cart,
        'categories': categories,
        'cart_total': cart.get_total_price(),
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Add product to session cart
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else '',
        }

    request.session['cart'] = cart
    return redirect('jwellery:cart_detail')  # make sure you have a cart_detail view
# Checkout with Razorpay
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('jwellery:product_list')

    items = list(cart)
    total_amount = int(cart.get_total_price() * 100)  # Razorpay needs amount in paise

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # Create order items
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['product'].price,
                    quantity=item['quantity']
                )

            # Create Razorpay order
            razorpay_order = razorpay_client.order.create(dict(
                amount=total_amount,
                currency='INR',
                payment_capture='0'  # manual capture
            ))

            order.razorpay_order_id = razorpay_order['id']
            order.save()

            categories = Category.objects.all()
            return render(request, 'jwellery/payment_page.html', {
                'order': order,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': total_amount,
                'currency': 'INR',
                'categories': categories,
                'cart': cart
            })
    else:
        form = OrderCreateForm()

    categories = Category.objects.all()
    return render(request, 'jwellery/checkout.html', {
        'cart': cart,
        'form': form,
        'categories': categories,
        'total': cart.get_total_price()
    })
@login_required
def wishlist_detail(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'jwellery/wishlist_detail.html', {'wishlist_items': wishlist_items})
# --- Wishlist views (session-based) ---
def add_to_wishlist(request, product_id):
    """
    Add product_id to wishlist stored in session.
    """
    product = get_object_or_404(Product, pk=product_id)
    wishlist = request.session.get('wishlist', [])

    # keep unique ids as strings
    pid = str(product_id)
    if pid not in wishlist:
        wishlist.append(pid)
        request.session['wishlist'] = wishlist
        request.session.modified = True
        messages.success(request, f"Added {product.title} to wishlist.")
    else:
        messages.info(request, f"{product.title} is already in your wishlist.")

    # safe redirect back
    return redirect(request.META.get('HTTP_REFERER', 'jwellery:product_list'))


def remove_from_wishlist(request, product_id):
    """
    Remove product_id from wishlist in session.
    """
    wishlist = request.session.get('wishlist', [])
    pid = str(product_id)
    if pid in wishlist:
        wishlist.remove(pid)
        request.session['wishlist'] = wishlist
        request.session.modified = True
        # optional message
        try:
            product = Product.objects.get(pk=product_id)
            messages.success(request, f"Removed {product.title} from wishlist.")
        except Product.DoesNotExist:
            pass
    else:
        messages.info(request, "Item not found in wishlist.")

    return redirect(request.META.get('HTTP_REFERER', 'jwellery:wishlist'))


# Payment Success
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # Verify payment
            razorpay_client.utility.verify_payment_signature(params_dict)
            order.paid = True
            order.razorpay_payment_id = payment_id
            order.save()

            # Clear cart
            cart = Cart(request)
            cart.clear()

            return redirect('jwellery:order_success', order_id=order.id)

        except razorpay.errors.SignatureVerificationError:
            return render(request, 'jwellery/payment_failed.html', {'order': order})

    return redirect('jwellery:product_list')

# Order Success
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'jwellery/order_success.html', {'order': order})
