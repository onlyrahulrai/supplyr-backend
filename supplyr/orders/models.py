from django.db import models
from django_mysql.models import EnumField


class Order(models.Model):

    class OrderStatusChoice(models.TextChoices):
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Approval'
        APPROVED = 'approved', 'Approved'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPATCHED = 'dispatched', 'Dispatched'
        DELIVERED = 'delivered', 'Delivered'


    buyer = models.ForeignKey('core.BuyerProfile', related_name='orders', on_delete=models.RESTRICT)
    seller = models.ForeignKey('core.SellerProfile', related_name='received_orders', on_delete=models.RESTRICT)
    status = EnumField(choices=OrderStatusChoice.choices, default=OrderStatusChoice.AWAITING_APPROVAL)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = EnumField(
        choices=('buyer', 'seller', 'staff'),
        blank=True, null=True
        )
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    address = models.ForeignKey('profiles.BuyerAddress', on_delete=models.RESTRICT)
    
    @property
    def featured_image(self):
        for item in self.items.all():
            if im := item.featured_image:
                return im


    class Meta:

        verbose_name = 'Order'
        verbose_name_plural = 'Orders'


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='items')
    product_variant = models.ForeignKey('inventory.Variant', on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def featured_image(self):
        if im := self.product_variant.featured_image:
            return im
        return None

    class Meta:

        verbose_name = 'OrderItem'
        verbose_name_plural = 'OrderItems'

