from django.urls import path
from . import views

app_name = 'jwellery'

urlpatterns = [
    path('', views.home, name='home'),                 
    path('about/', views.about_view, name='about'),    
    path('signup/', views.signup_view, name='signup'), 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),

    # Cart URLs
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
 path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

path('wishlist/', views.wishlist_detail, name='wishlist'),
path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('payment-success/', views.payment_success, name='payment_success'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
   

    # Product detail last
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]
