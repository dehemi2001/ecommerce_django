from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import Account, UserProfile
from store.models import Category, Product, ProductConfiguration, Attribute, AttributeValue
from carts.models import CartItem


class CodOrderPlacementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Account.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.user.phone_number = '+94771234567'
        self.user.is_active = True
        self.user.save()
        UserProfile.objects.get_or_create(user=self.user)

        self.category = Category.objects.create(category_name='Test Category', slug='test-category')
        dummy_image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        self.product = Product.objects.create(
            product_name='Test Product',
            slug='test-product',
            category=self.category,
            images=dummy_image,
        )
        self.attr_color = Attribute.objects.create(name='Color')
        self.attr_spec = Attribute.objects.create(name='Specification')
        self.color_red = AttributeValue.objects.create(attribute=self.attr_color, value='Red')
        self.spec_256gb = AttributeValue.objects.create(attribute=self.attr_spec, value='256GB')
        self.config = ProductConfiguration.objects.create(
            product=self.product,
            stock=10,
            price=Decimal('100.00'),
        )
        self.config.attribute_values.set([self.color_red, self.spec_256gb])
        self.config.save()

        self.cart_item = CartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=2,
            is_active=True,
        )
        self.cart_item.attribute_values.set([self.color_red, self.spec_256gb])

    def test_place_cod_order(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        place_order_url = reverse('place_order')
        response = self.client.post(place_order_url, {
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+94771234567',
            'email': 'testuser@example.com',
            'address_line_1': '123 Test St',
            'address_line_2': '',
            'country': 'Sri Lanka',
            'state': 'Western',
            'city': 'Colombo',
            'order_note': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/payments.html')

        from orders.models import Order
        order = Order.objects.filter(user=self.user, is_ordered=False).first()
        self.assertIsNotNone(order)

        payments_url = reverse('payments')
        response = self.client.post(
            payments_url,
            data={'orderID': order.order_number, 'payment_method': 'cod'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('order_number', data)
        self.assertIn('transID', data)

        order.refresh_from_db()
        self.assertTrue(order.is_ordered)
        self.assertIsNotNone(order.payment)
        self.assertEqual(order.payment.payment_method, 'COD')
        self.assertEqual(order.payment.status, 'Pending')

        from orders.models import OrderProduct
        self.assertTrue(OrderProduct.objects.filter(order=order).exists())
        self.assertEqual(CartItem.objects.filter(user=self.user, is_active=True).count(), 0)

        self.config.refresh_from_db()
        self.assertEqual(self.config.stock, 8)
