from .models import Company


def company(request):
    obj = Company.objects.first()
    if obj is None:
        # Safety net; the data migration normally creates the single row.
        obj = Company.objects.create()
    return {'company': obj}
