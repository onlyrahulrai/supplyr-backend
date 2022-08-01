import pandas as pd
import random
from supplyr.inventory.models import Product, Variant, Category
from supplyr.profiles.models import SellerProfile

csv = pd.read_csv("MOCK_DATA.csv")

cats = list(Category.objects.all())
owner = SellerProfile.objects.first()


for i,r in csv.iterrows():
    title=r['title']
    description = r['description']
    quantity = r['quantity']
    price = r['price']
    actual_price = r['actual_price']
    pr = Product.objects.create(title = title, description=description, owner=owner)
    pr.sub_categories.set(random.sample(cats, random.randint(1,3)))
    var = Variant.objects.create(product = pr, option1_name = 'default', option1_value='default', quantity=quantity, price=price, actual_price=actual_price)
    print("Entered product: ", title)
