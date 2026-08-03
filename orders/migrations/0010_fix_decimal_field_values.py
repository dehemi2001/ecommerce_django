from django.db import migrations


def fix_decimal_values(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id, amount_paid, usd_amount FROM orders_payment")
        rows = cursor.fetchall()
        for row in rows:
            payment_id, amount_paid, usd_amount = row
            new_amount = float(amount_paid) if amount_paid not in ('', None) else None
            new_usd = float(usd_amount) if usd_amount not in ('', None) else None
            cursor.execute(
                "UPDATE orders_payment SET amount_paid = %s, usd_amount = %s WHERE id = %s",
                [new_amount, new_usd, payment_id]
            )


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_order_order_total_alter_orderproduct_product_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_decimal_values, migrations.RunPython.noop),
    ]
