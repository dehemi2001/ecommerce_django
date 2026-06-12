from django.shortcuts import render
from store.models import Product, ReviewRating
from django.db.models import Avg, Q

def home(request):
    # Get top 8 products based on average rating of approved reviews
    products = Product.objects.filter(is_available=True).annotate(
        avg_rating=Avg('reviewrating__rating', filter=Q(reviewrating__status=True))
    ).order_by('-avg_rating', '-created_date')[:8]

    context = {
        'products': products,
    }
    return render(request, 'home.html', context)