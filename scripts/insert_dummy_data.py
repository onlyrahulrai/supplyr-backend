from django.utils.lorem_ipsum import words
from django.template.defaultfilters import capfirst
from random import randint

from supplyr.inventory.models import Category, SubCategory


camel_case = lambda value:' '.join(list(map(lambda x:capfirst(x), value.split(' '))))
class formatted:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def printc(formatting, value):
    print(getattr(formatted, formatting) + value + formatted.END)

def run():
    try:
        if not Category.objects.exists():
            printc("YELLOW", "Creating Categories and SubCategories")
            sub_serial = 1
            for i in range(10):
                c = Category.objects.create(
                    name=camel_case(words(randint(1,3), False)),
                    serial=i
                    )
                for i in range(randint(7,20)):
                    SubCategory.objects.create(
                        name = camel_case(words(randint(1,3), False)),
                        serial = sub_serial,
                        category = c
                        )
                    sub_serial +=1
                print("Created Category: ", c.name)
            
            printc ("GREEN", "Created dummy categories and subcategories")
        else:
            printc ("RED", "Categories already exist. Aborting.")
    except Exception as e:
        Throw(e)
    else:
        print("Script run successfully")