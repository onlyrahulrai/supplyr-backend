from re import T
from django.db import models
from django_extensions.db.fields import AutoSlugField
from django_mysql.models import EnumField
from supplyr.profiles.models import SellerProfile

class Order(models.Model):

    class OrderStatusChoice(models.TextChoices):
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Approval'
        APPROVED = 'approved', 'Approved'
        PROCESSED = 'processed', 'Processed'
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
    discount = models.DecimalField(default=0,max_digits=12, decimal_places=2)
    total_extra_discount = models.DecimalField(default=0,max_digits=12, decimal_places=2)
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
    extra_discount = models.DecimalField(default=0,max_digits=12, decimal_places=2)
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

class OrderStatusChoices(models.Model):
    name = models.CharField(max_length=40)
    slug = AutoSlugField(max_length=40, editable=True, populate_from=['name'], unique=True)
    serial = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ('serial',)
    
    def __str__(self):
        return self.name

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
        
        
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50,null=True,blank=True)
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="invoices")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        verbose_name_plural = 'Invoices'


class OrderStatusVariable(models.Model):
    class DataTypeChoices(models.TextChoices):
        TEXT = 'text', 'Text'
        DATE = 'date', 'Date'
        NUMBER = 'number', 'Number'

    name = models.CharField(max_length=100)
    slug = AutoSlugField(max_length=100, editable=True, populate_from=['name'])
    data_type = EnumField(choices=DataTypeChoices.choices, default=DataTypeChoices.TEXT)
    linked_order_status = models.ForeignKey(OrderStatusChoices, on_delete=models.RESTRICT)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sellers = models.ManyToManyField(SellerProfile, related_name='order_status_variables')

    def __str__(self):
        return self.name

# class OrderStatusVariableSellerMapping(models.Model):
#     variable = models.ForeignKey(OrderStatusVariable, related_name="status_variable_mappings")
#     seller = models.ForeignKey(SellerProfile, related_name="order_status_variable_mappings")
#     created_at = models.DateTimeField(auto_now_add=True)

class OrderStatusVariableValue(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_variable_values')
    variable = models.ForeignKey(OrderStatusVariable, on_delete=models.RESTRICT, related_name="values")
    value = models.TextField(blank=True, null=True)



