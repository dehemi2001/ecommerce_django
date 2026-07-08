from django.conf import settings
from django.core.files import File
from django.db import migrations

import os


ABOUT_US = """
<p>
    <strong>Solid Computers</strong> is Negombo's premier destination for high-end computing
    hardware and personalized tech solutions. Since opening our doors, we have been committed
    to delivering excellence in both performance and service.
</p>
<p>
    Our team of passionate technology enthusiasts carefully curates every product we offer,
    ensuring our customers have access to reliable components, the latest hardware, and
    expert guidance for building and upgrading their systems.
</p>
<p>
    Whether you are a gamer, a content creator, a professional, or a first-time buyer, we are
    here to help you find the right solution at the right price. Thank you for choosing
    Solid Computers.
</p>
<h4 class="mt-4">Our Mission</h4>
<p>
    To provide Sri Lankan customers with world-class computing hardware and trustworthy,
    personalized service &mdash; making high-performance technology accessible to everyone.
</p>
"""

TERMS_CONDITIONS = """
<p class="text-muted">
    Welcome to Solid Computers. By accessing or using our website and placing an order,
    you agree to be bound by the following terms and conditions. Please read them carefully.
</p>

<h5 class="mt-4">1. Orders &amp; Pricing</h5>
<p>
    All prices are listed in Sri Lankan Rupees (LKR) unless stated otherwise. We reserve the
    right to refuse or cancel any order at our discretion, including orders with incorrect
    pricing or availability errors.
</p>

<h5 class="mt-4">2. Payment</h5>
<p>
    We accept PayPal and Cash on Delivery (for eligible orders). For PayPal payments,
    LKR amounts are converted to USD at the live exchange rate at the time of checkout.
</p>

<h5 class="mt-4">3. Delivery</h5>
<p>
    Delivery timelines are estimates and are not guaranteed. Risk of loss passes to the
    customer upon delivery. For Cash on Delivery orders, payment is due in full at the time
    of delivery.
</p>

<h5 class="mt-4">4. Returns &amp; Refunds</h5>
<p>
    Products may be returned in their original condition within the period specified at the
    time of purchase. Refunds will be processed using the original payment method where possible.
</p>

<h5 class="mt-4">5. Limitation of Liability</h5>
<p>
    Solid Computers shall not be liable for any indirect, incidental, or consequential damages
    arising from the use of this website or its products.
</p>

<p class="text-muted mt-4">
    These terms are a placeholder and may be updated at any time. Continued use of the site
    constitutes acceptance of the current terms.
</p>
"""

PRIVACY_POLICY = """
<p class="text-muted">
    Your privacy matters to us. This policy describes the information we collect and how we
    use it when you use the Solid Computers website.
</p>

<h5 class="mt-4">1. Information We Collect</h5>
<p>
    We collect information you provide directly, such as your name, email address, phone number,
    shipping address, and order details when you place an order or contact us.
</p>

<h5 class="mt-4">2. How We Use Your Information</h5>
<p>
    We use your information to process orders, deliver products, provide customer support, and
    improve our services. We do not sell your personal information to third parties.
</p>

<h5 class="mt-4">3. Payments</h5>
<p>
    Payments processed through PayPal are handled by PayPal's secure platform. We do not store
    your full payment card details on our servers.
</p>

<h5 class="mt-4">4. Cookies</h5>
<p>
    We use cookies to maintain your session, remember your cart, and understand how our site is
    used. You can disable cookies in your browser, though some features may not function properly.
</p>

<h5 class="mt-4">5. Your Rights</h5>
<p>
    You may request access to, correction of, or deletion of your personal information by
    contacting us at solidcomputers@outlook.com.
</p>

<p class="text-muted mt-4">
    This privacy policy is a placeholder and may be updated from time to time.
</p>
"""


def seed_company(apps, schema_editor):
    Company = apps.get_model('company', 'Company')
    if Company.objects.exists():
        return

    company = Company.objects.create(
        name='Solid Computers',
        description="Negombo's premier destination for high-end computing hardware and "
                    "personalized tech solutions. Excellence in performance and service.",
        address='444 Puttalam - Colombo Rd, Negombo',
        email='solidcomputers@outlook.com',
        phone='+94 76 348 9449',
        open_hours='Mon - Sat: 9:00 AM - 7:00 PM',
        about_us=ABOUT_US,
        terms_conditions=TERMS_CONDITIONS,
        privacy_policy=PRIVACY_POLICY,
    )

    static_img = os.path.join(settings.BASE_DIR, 'ecommerce_django', 'static', 'images')

    logo = os.path.join(static_img, 'logo3.png')
    if os.path.exists(logo):
        with open(logo, 'rb') as f:
            company.logo.save('logo.png', File(f), save=True)

    cover = os.path.join(static_img, 'banners', 'cover.jpg')
    if os.path.exists(cover):
        with open(cover, 'rb') as f:
            company.cover_image.save('cover.jpg', File(f), save=True)


def remove_company(apps, schema_editor):
    Company = apps.get_model('company', 'Company')
    Company.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_company, remove_company),
    ]
