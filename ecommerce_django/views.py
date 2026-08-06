from django.shortcuts import render
from store.models import Product, ReviewRating
from category.models import Category
from django.db.models import Avg, Q


def home(request):
    categories = Category.objects.filter(is_deleted=False)
    categories_products = {}
    for category in categories:
        products = Product.objects.filter(
            is_available=True,
            category=category,
        ).annotate(
            avg_rating=Avg(
                'reviewrating__rating',
                filter=Q(reviewrating__status=True),
            )
        ).order_by('-avg_rating', '-created_date')[:4]
        if products.exists():
            categories_products[category] = products

    context = {
        'categories_products': categories_products,
    }
    return render(request, 'home.html', context)


def about_us(request):
    return render(request, 'pages/about_us.html')


def contact_us(request):
    return render(request, 'pages/contact_us.html')


def terms_conditions(request):
    return render(request, 'pages/terms_conditions.html')


def privacy_policy(request):
    return render(request, 'pages/privacy_policy.html')
