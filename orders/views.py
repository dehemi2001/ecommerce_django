from django.template import context
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm
import datetime
from django.db.models import Count
from .models import Order, Payment, OrderProduct
from .currency import convert_lkr_to_usd
import json
from store.models import Product, ProductConfiguration
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from company.models import Company

# Create your views here.

def finalize_order(request, order, payment):
    """Move cart items to OrderProduct, reduce stock, clear cart and email the customer.

    Shared by both the PayPal and Cash on Delivery flows so the post-payment work is
    identical regardless of payment method.
    """
    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.price
        orderproduct.ordered = True
        orderproduct.save()

        product_attribute_values = item.attribute_values.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.attribute_values.set(product_attribute_values)
        orderproduct.save()

        # Reduce the quantity of the specific configuration sold
        configurations = ProductConfiguration.objects.annotate(
            av_count=Count('attribute_values', distinct=True)
        ).filter(product=item.product, av_count=len(product_attribute_values))
        for av in product_attribute_values:
            configurations = configurations.filter(attribute_values=av)

        configuration = configurations.first()

        if configuration:
            configuration.stock -= item.quantity
            configuration.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send the invoice as an HTML email (with a plain-text fallback)
    mail_subject = 'Thank you for your order!'

    ordered_products = OrderProduct.objects.filter(order=order)
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
    }, request=request)

    text_message = (
        f"Hi {order.first_name},\n\n"
        f"Thank you for your order!\n\n"
        f"Order Number: {order.order_number}\n"
        f"Grand Total: LKR {order.order_total}\n"
    )

    try:
        to_email = request.user.email
        email = EmailMultiAlternatives(mail_subject, text_message, to=[to_email])
        if mime_logo is not None:
            email.attach(mime_logo)
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception:
        # Don't fail the order just because the confirmation email couldn't be sent.
        pass


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.filter(user=request.user, is_ordered=False, order_number=body['orderID']).first()

    # Idempotency guard: if the order was already finalized (e.g. COD button double
    # clicked or the page was refreshed) just return its existing details.
    if order is None:
        existing = Order.objects.filter(user=request.user, order_number=body['orderID'], is_ordered=True).first()
        if existing and existing.payment:
            return JsonResponse({
                'order_number': existing.order_number,
                'transID': existing.payment.payment_id,
            })
        return JsonResponse({'error': 'Order not found'}, status=404)

    payment_method = body.get('payment_method')

    if payment_method == 'cod':
        payment = Payment(
            user = request.user,
            payment_id = f"COD-{order.order_number}",
            payment_method = 'COD',
            amount_paid = order.order_total,
            usd_amount = '',
            status = 'Pending',
        )
        payment.save()
        order.payment = payment
        order.is_ordered = True
        order.save()
        finalize_order(request, order, payment)
    else:
        # Store transaction details inside Payment model (PayPal)
        payment = Payment(
            user = request.user,
            payment_id = body['transID'],
            payment_method = body['payment_method'],
            amount_paid = order.order_total,
            usd_amount = body.get('usd_amount', ''),
            status = body['status'],
        )
        payment.save()
        order.payment = payment
        order.is_ordered = True
        order.save()
        finalize_order(request, order, payment)

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

def place_order(request, total=0, quantity=0,):
    current_user = request.user
    
    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    for cart_item in cart_items:
        total += (cart_item.price * cart_item.quantity)
        quantity += cart_item.quantity
    grand_total = total

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'grand_total': grand_total,
                'paypal_amount': convert_lkr_to_usd(grand_total),
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id = transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal' : subtotal,
        }       
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')