from decimal import Decimal
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from company.models import Company


def send_order_invoice_email(order, payment, user_email=None, mail_subject=''):
    if user_email is None:
        user_email = order.email

    ordered_products = order.orderproduct_set.all()
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)

    company = Company.objects.first()
    logo_cid = None
    mime_logo = None
    if company and company.logo:
        try:
            import os
            from email.mime.image import MIMEImage
            logo_path = company.logo.path
            with open(logo_path, 'rb') as f:
                ext = os.path.splitext(logo_path)[1].lower().lstrip('.')
                subtype = 'jpeg' if ext == 'jpg' else (ext or 'png')
                mime_logo = MIMEImage(f.read(), _subtype=subtype)
            mime_logo.add_header('Content-ID', '<logo>')
            mime_logo.add_header('Content-Disposition', 'inline', filename='logo.png')
            logo_cid = 'logo'
        except (FileNotFoundError, OSError):
            logo_cid = None

    html_message = render_to_string('orders/order_invoice_email.html', {
        'order': order,
        'ordered_products': ordered_products,
        'subtotal': subtotal,
        'payment': payment,
        'company': company,
        'logo_cid': logo_cid,
    })

    text_message = (
        f"Hi {order.first_name},\n\n"
        f"{mail_subject}\n\n"
        f"Order Number: {order.order_number}\n"
        f"Grand Total: LKR {order.order_total}\n"
    )

    try:
        from_email = f"{company.name} <{settings.EMAIL_HOST_USER}>" if company else settings.EMAIL_HOST_USER
        email = EmailMultiAlternatives(mail_subject, text_message, from_email, to=[user_email])
        if mime_logo is not None:
            email.attach(mime_logo)
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception:
        pass
