from re import T
from django.db import models
from django_extensions.db.fields import AutoSlugField
from django_mysql.models import EnumField
from supplyr.profiles.models import SellerProfile
from functools import reduce
from num2words import num2words

class Order(models.Model):

    class OrderStatusChoice(models.TextChoices):
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Approval'
        APPROVED = 'approved', 'Approved'
        PROCESSED = 'processed', 'Processed'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPATCHED = 'dispatched', 'Dispatched'
        DELIVERED = 'delivered', 'Delivered'
        RETURNED = "returned","Returned"

    buyer = models.ForeignKey('profiles.BuyerProfile', related_name='orders', on_delete=models.RESTRICT)
    order_number = models.CharField(max_length=200)
    seller = models.ForeignKey('profiles.SellerProfile', related_name='received_orders', on_delete=models.RESTRICT)
    status = EnumField(choices=OrderStatusChoice.choices, default=OrderStatusChoice.AWAITING_APPROVAL)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=False)
    created_by = models.ForeignKey('core.User', related_name='orders_created', on_delete=models.RESTRICT)
    cancelled_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    cancelled_by = EnumField(
        choices=('buyer', 'seller', 'staff', 'sales'),
        blank=True, null=True
        )
    taxable_amount = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    sgst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    cgst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    igst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    subtotal = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    # total_subamount = models.DecimalField(default=0,max_digits=14,decimal_places=2)
    total_extra_discount = models.DecimalField(default=0,max_digits=12, decimal_places=2)
    address = models.ForeignKey('profiles.BuyerAddress', on_delete=models.RESTRICT,null=True,blank=True)
    source = models.CharField(max_length=78, null=True, blank=True)

    salesperson = models.ForeignKey('profiles.SalespersonProfile', on_delete=models.RESTRICT, blank=True, null=True, related_name='orders') # Populated when order is placed by a salesperson
    
    @property
    def tax_amount(self):
        return self.igst + self.sgst + self.cgst
    
    @property
    def featured_image(self):
        for item in self.items.all():
            if im := item.featured_image:
                return im

    
    @property
    def total_amount_in_text(self):
        return num2words(self.total_amount)

    @property
    def is_global_fulfillment(self):
        statuses = set([item.order_group.status if item.order_group else item.status for item in self.items.all()])
        
        print("Statuses: ",set([item.order_group.status if item.order_group else item.status for item in self.items.all()]))
        
        return (len(statuses) == 1)

    class Meta:

        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        unique_together = ["seller","order_number"]
        
    def __str__(self):
        return f"{self.id} {self.buyer} {self.seller}"

class OrderGroup(models.Model):
    #group_index = # order wise group serial number 1,2,3..  
    group_index = models.CharField(max_length=200)
    parent = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="groups")
    is_paid = models.BooleanField(default=False)
    status = EnumField(choices=Order.OrderStatusChoice.choices,default=Order.OrderStatusChoice.APPROVED)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def prices(self):
        
        ordergroup_calculation = {
            "subtotal": 0,
            "extra_discount": 0,
            "igst": 0,
            "cgst": 0,
            "sgst": 0,
            "taxable_amount": 0,
            'total_amount': 0,
            'tax_amount':0
        }
        
        for item in self.items.all():
            ordergroup_calculation["subtotal"] += item.subtotal 
            ordergroup_calculation["extra_discount"] += (item.extra_discount * item.quantity)
            ordergroup_calculation[ "igst"] += item.igst
            ordergroup_calculation["cgst"] += item.cgst
            ordergroup_calculation["sgst"] += item.sgst
            ordergroup_calculation["taxable_amount"] += item.taxable_amount
            ordergroup_calculation['total_amount'] += item.total_amount
            ordergroup_calculation['tax_amount'] += (item.igst + item.cgst + item.sgst)
                
        return ordergroup_calculation
        
    @property
    def total_amount_in_text(self):
        return num2words(self.prices.get("total_amount"))
    
    class Meta:
        unique_together = ["parent","group_index"]

class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='items')
    order_group = models.ForeignKey(OrderGroup, on_delete=models.SET_NULL, related_name='items',null=True,blank=True)
    status = EnumField(choices=Order.OrderStatusChoice.choices,default=Order.OrderStatusChoice.AWAITING_APPROVAL)
    product_variant = models.ForeignKey('inventory.Variant', on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    extra_discount = models.DecimalField(default=0,max_digits=12, decimal_places=2)
    taxable_amount = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    cgst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    sgst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    igst = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    subtotal = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    actual_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    

    is_active = models.BooleanField(default=True)
    item_note = models.TextField(blank=True, null=True)

    @property
    def tax_amount(self):
        return round((self.igst + self.cgst + self.sgst),2)
    

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
    order_group = models.ForeignKey(OrderGroup, on_delete=models.RESTRICT,related_name='history',null=True,blank=True)
    items = models.ManyToManyField(OrderItem)
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
    order_group = models.ForeignKey(OrderGroup, on_delete=models.SET_NULL,null=True,blank=True ,related_name="invoices")
    invoice_pdf  = models.FileField(upload_to='invoice_pdfs/', null=True, blank=True)
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
    is_internal = models.BooleanField(default=False)   # Internal status variables won't be visible to the buyers
    slug = AutoSlugField(max_length=100, editable=True, populate_from=['name'])
    data_type = EnumField(choices=DataTypeChoices.choices, default=DataTypeChoices.TEXT)
    linked_order_status = models.ForeignKey(OrderStatusChoices, on_delete=models.RESTRICT)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sellers = models.ManyToManyField(SellerProfile, related_name='order_status_variables')

    def __str__(self):
        return self.name

class OrderStatusVariableValue(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_variable_values')
    order_group = models.ForeignKey(OrderGroup, on_delete=models.SET_NULL,null=True,related_name='status_variable_values')
    variable = models.ForeignKey(OrderStatusVariable, on_delete=models.RESTRICT, related_name="values")
    value = models.TextField(blank=True, null=True)

class Payment(models.Model):
    class PaymentMode(models.TextChoices):
        Cheque = 'cheque','Cheque'
        Cash = 'cash','Cash'
        BankTransfer = 'banktransfer','BankTransfer'
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE,related_name="transactions")
    buyer = models.ForeignKey('profiles.BuyerProfile', on_delete=models.CASCADE,related_name="transactions")
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    mode = EnumField(choices=PaymentMode.choices,default=PaymentMode.BankTransfer)
    remarks = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    date    = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f'{self.seller} - {self.buyer} - {self.amount}' 

class Ledger(models.Model):
    class TransactionTypeChoice(models.TextChoices):
        ORDER_CREATED="order_created","Order Created"
        PAYMENT_ADDED="payment_added","Payment Added"
        ORDER_CANCELLED="order_cancelled","Order Cancelled"
        ORDER_RETURNED = "order_returned","Order Returned"
        ORDER_PAID = "order_paid","Order Paid"
    
    transaction_type  = EnumField(choices=TransactionTypeChoice.choices,default=TransactionTypeChoice.ORDER_CREATED)
    order_group = models.ForeignKey(OrderGroup, on_delete=models.SET_NULL,null=True)
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE,related_name="ledgers",null=True,blank=True)
    buyer = models.ForeignKey('profiles.BuyerProfile', on_delete=models.CASCADE,related_name="ledgers",null=True,blank=True)
    amount = models.DecimalField(default=0,decimal_places=2,max_digits=12)
    balance = models.DecimalField(default=0,decimal_places=2,max_digits=12)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE,related_name="ledgers",null=True,blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="ledgers",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def description(self):
        description_str = None
        if self.transaction_type == self.TransactionTypeChoice.PAYMENT_ADDED:
            description_str = f"Payment added. Payment ID: {self.payment.id}"
        elif self.transaction_type == self.TransactionTypeChoice.ORDER_CREATED:
            description_str = f"Order #{self.order.id} created by {'you' if self.order.created_by == self.seller.owner else 'buyer' }"
        elif self.transaction_type == self.TransactionTypeChoice.ORDER_CANCELLED:
            print(vars(self.order))
            description_str = f"Order #{self.order.id} cancelled by {'you' if self.order.cancelled_by == 'seller' else 'buyer' if self.order.cancelled_by == 'buyer' else ''  }"
        else:
            description_str = f"Order #{self.order.id} mark as paid by {'you' if self.order.created_by == self.seller.owner else 'buyer' }"
        return description_str