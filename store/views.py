from orders.models import OrderProduct
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from store.models import Product, ReviewRating, ProductGallery, Attribute, AttributeValue, ProductConfiguration
from django.contrib import messages
from django.shortcuts import redirect
from category.models import Category
from django.db.models import Q, Min
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.db.models import Count
from .forms import ReviewForm

# Create your views here.

def _filter_attributes():
    """Attributes (and their values) that are actually used by available products."""
    attributes = Attribute.objects.filter(
        values__productconfiguration__product__is_available=True
    ).distinct()
    for attr in attributes:
        attr.used_values = attr.values.filter(
            productconfiguration__product__is_available=True
        ).distinct()
    return attributes


def _apply_product_filters(products, request):
    """Faceted filtering: OR within an attribute, AND across attributes, plus price range."""
    selected = {}
    for key, vals in request.GET.lists():
        if key.startswith('attr_') and vals:
            try:
                attr_id = int(key[len('attr_'):])
            except ValueError:
                continue
            ids = [int(v) for v in vals if v.isdigit()]
            if ids:
                products = products.filter(
                    configurations__is_active=True,
                    configurations__attribute_values__id__in=ids,
                ).distinct()
                selected[attr_id] = ids

    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    if min_p or max_p:
        products = products.annotate(_min_price=Min('configurations__price'))
        if min_p:
            products = products.filter(_min_price__gte=min_p)
        if max_p:
            products = products.filter(_min_price__lte=max_p)
        products = products.distinct()

    return products, selected, min_p, max_p


def _filter_context(request, products, selected, min_p, max_p, active_category=None):
    attributes = _filter_attributes()
    for attr in attributes:
        attr.selected_ids = set(selected.get(attr.id, []))
    get = request.GET.copy()
    get.pop('page', None)
    return {
        'products': products,
        'product_count': products.paginator.count if hasattr(products, 'paginator') else products.count(),
        'attributes': attributes,
        'min_price': min_p,
        'max_price': max_p,
        'filter_query': get.urlencode(),
        'active_category': active_category,
    }


def store(request, category_slug=None):
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)

    products, selected, min_p, max_p = _apply_product_filters(products, request)
    products = products.order_by('id')

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = _filter_context(request, paged_products, selected, min_p, max_p, active_category=category_slug)
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(
        product_id=single_product.id, status=True
    ).select_related('user__userprofile')
    for r in reviews:
        avatar = None
        try:
            prof = r.user.userprofile
            if prof and prof.profile_picture:
                avatar = prof.profile_picture.url
        except Exception:
            pass
        r.avatar_url = avatar

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    products = Product.objects.none()
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
                is_available=True,
            )

    products, selected, min_p, max_p = _apply_product_filters(products, request)
    products = products.order_by('-created_date')

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = _filter_context(request, paged_products, selected, min_p, max_p)
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)

def get_variation_stock(request):
    if request.method != 'GET':
        return JsonResponse({'stock': 0, 'message': 'Invalid request method.'}, status=405)

    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'stock': 0, 'message': 'Product ID missing.'}, status=400)

    # Collect attribute parameters from request, ignoring empty values and CSRF token
    selected_attributes = {}
    for key, value in request.GET.items():
        if key in ['product_id', 'csrfmiddlewaretoken'] or not value:
            continue
        selected_attributes[key] = value.strip()

    if not selected_attributes:
        return JsonResponse({'stock': 0, 'message': 'Please select all options.'}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'stock': 0, 'message': 'Product not found.'}, status=404)

    # Retrieve the AttributeValue objects matching the selected criteria
    attribute_value_objs = []
    for category, val in selected_attributes.items():
        try:
            # Find the attribute value globally by matching its attribute name (e.g. "color", "specification")
            # and its value. No product filter needed since these are global.
            attribute_value = AttributeValue.objects.get(
                attribute__name__iexact=category,
                value__iexact=val,
            )
            attribute_value_objs.append(attribute_value)
        except AttributeValue.DoesNotExist:
            return JsonResponse({'stock': 0, 'message': f'Selected value not found: {category}={val}.'}, status=404)

    # Filter configurations that contain all selected attribute values and have the exact same number
    configurations_qs = ProductConfiguration.objects.annotate(
        av_count=Count('attribute_values', distinct=True)
    ).filter(product=product, is_active=True, av_count=len(attribute_value_objs))
    for av in attribute_value_objs:
        configurations_qs = configurations_qs.filter(attribute_values=av)

    configuration = configurations_qs.first()

    stock = configuration.stock if configuration else 0
    price = configuration.price if configuration else product.price
    message = f"In Stock: {stock}" if stock > 0 else "Out of Stock"
    return JsonResponse({'stock': stock, 'price': price, 'message': message})