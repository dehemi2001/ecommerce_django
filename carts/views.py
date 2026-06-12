from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.db.models import Count
from store.models import Product, Variation, ProductConfiguration
from .models import Cart, CartItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product, 
                    variation_category__iexact=key.strip(), 
                    variation_value__iexact=value.strip()
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # Find the specific configuration matching these variations
    configurations = ProductConfiguration.objects.filter(product=product, is_active=True)
    for v in product_variation:
        configurations = configurations.filter(variations=v)
    
    # Ensure exact match (same number of variations)
    configuration = configurations.annotate(v_count=Count('variations', distinct=True)).filter(v_count=len(product_variation)).first()

    if not configuration or configuration.stock <= 0:
        messages.error(request, "Sorry, this specific combination is currently out of stock.")
        return redirect(product.get_url())

    # Get existing items for this product based on auth status
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    # Check if a CartItem with the exact same variations already exists
    existing_item = None
    for item in cart_items:
        # Sort both lists by ID to ensure consistent comparison
        if sorted(list(item.variations.all()), key=lambda x: x.id) == sorted(product_variation, key=lambda x: x.id):
            existing_item = item
            break

    if existing_item:
        existing_item.quantity += 1
        existing_item.save()
    else:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=request.user if request.user.is_authenticated else None,
            cart=None if request.user.is_authenticated else cart
        )
        if product_variation:
            cart_item.variations.set(product_variation)
        cart_item.save()

    return redirect('cart')

def get_cart_summary(request):
    """Helper function to calculate cart totals for cart and checkout views."""
    total, quantity = 0, 0
    cart_items = None
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    tax = (2 * total) / 100
    return {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': total + tax,
    }

def cart(request, total=0, quantity=0, cart_items=None):
    return render(request, 'store/cart.html', get_cart_summary(request))

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    return render(request, 'store/checkout.html', get_cart_summary(request))

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass # just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass # just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)