from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.db.models import Count
from store.models import Product, AttributeValue, ProductConfiguration
from .models import Cart, CartItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def merge_cart(request, user):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart)

        for item in cart_items:
            user_items = CartItem.objects.filter(product=item.product, user=user)
            existing_item = None
            for ui in user_items:
                if sorted(list(ui.attribute_values.all()), key=lambda x: x.id) == \
                   sorted(list(item.attribute_values.all()), key=lambda x: x.id):
                    existing_item = ui
                    break

            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
                item.delete()
            else:
                item.user = user
                item.cart = None
                item.save()
    except Cart.DoesNotExist:
        pass

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_attribute_values = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                # Look up the global AttributeValue by attribute name and value
                attribute_value = AttributeValue.objects.get(
                    attribute__name__iexact=key.strip(), 
                    value__iexact=value.strip()
                )
                product_attribute_values.append(attribute_value)
            except AttributeValue.DoesNotExist:
                pass

    # Find the specific configuration matching these attribute values
    configurations = ProductConfiguration.objects.annotate(
        av_count=Count('attribute_values', distinct=True)
    ).filter(product=product, is_active=True, av_count=len(product_attribute_values))
    for av in product_attribute_values:
        configurations = configurations.filter(attribute_values=av)
    
    configuration = configurations.first()

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

    # Check if a CartItem with the exact same attribute values already exists
    existing_item = None
    for item in cart_items:
        # Sort both lists by ID to ensure consistent comparison
        if sorted(list(item.attribute_values.all()), key=lambda x: x.id) == sorted(product_attribute_values, key=lambda x: x.id):
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
        if product_attribute_values:
            cart_item.attribute_values.set(product_attribute_values)
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
            total += (cart_item.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    return {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': total,
    }

def cart(request, total=0, quantity=0, cart_items=None):
    return render(request, 'store/cart.html', get_cart_summary(request))

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    context = get_cart_summary(request)
    user = request.user
    profile = getattr(user, 'userprofile', None)
    context['initial'] = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone_number,
        'address_line_1': profile.address_line_1 if profile else '',
        'address_line_2': profile.address_line_2 if profile else '',
        'city': profile.city if profile else '',
        'state': profile.state if profile else '',
        'country': profile.country if profile else '',
        'order_note': '',
    }
    return render(request, 'store/checkout.html', context)

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