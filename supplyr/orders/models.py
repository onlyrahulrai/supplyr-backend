from re import T
from django.db import models
from django_mysql.models import EnumField


class Order(models.Model):

    class OrderStatusChoice(models.TextChoices):
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Approval'
        APPROVED = 'approved', 'Approved'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPATCHED = 'dispatched', 'Dispatched'
        DELIVERED = 'delivered', 'Delivered'


    buyer = models.ForeignKey('profiles.BuyerProfile', related_name='orders', on_delete=models.RESTRICT)
    seller = models.ForeignKey('profiles.SellerProfile', related_name='received_orders', on_delete=models.RESTRICT)
    status = EnumField(choices=OrderStatusChoice.choices, default=OrderStatusChoice.AWAITING_APPROVAL)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('core.User', related_name='orders_created', on_delete=models.RESTRICT)
    cancelled_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    cancelled_by = EnumField(
        choices=('buyer', 'seller', 'staff', 'sales'),
        blank=True, null=True
        )
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    address = models.ForeignKey('profiles.BuyerAddress', on_delete=models.RESTRICT)

    salesperson = models.ForeignKey('profiles.SalespersonProfile', on_delete=models.RESTRICT, blank=True, null=True, related_name='orders') # Populated when order is placed by a salesperson
    
    @property
    def featured_image(self):
        for item in self.items.all():
            if im := item.featured_image:
                return im


    class Meta:

        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.buyer} {self.seller}"


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='items')
    product_variant = models.ForeignKey('inventory.Variant', on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    actual_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    @property
    def featured_image(self):
        if im := self.product_variant.featured_image:
            return im

        elif im := self.product_variant.product.featured_image:
            return im

        return None

    class Meta:

        verbose_name = 'OrderItem'
        verbose_name_plural = 'OrderItems'

class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='history')
    status = EnumField(choices=Order.OrderStatusChoice.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.RESTRICT)
    salesperson = models.ForeignKey('profiles.SalespersonProfile', on_delete=models.RESTRICT, blank=True, null=True)
    seller = models.ForeignKey('profiles.SellerProfile', on_delete=models.RESTRICT, blank=True, null=True)
    buyer = models.ForeignKey('profiles.BuyerProfile', on_delete=models.RESTRICT, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Order Histories'
        ordering = ('-created_at',)


