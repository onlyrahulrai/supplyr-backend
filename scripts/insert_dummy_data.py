from django.utils.lorem_ipsum import words
from django.template.defaultfilters import capfirst
from random import randint

from supplyr.core.models import Category, SubCategory


camel_case = lambda value:' '.join(list(map(lambda x:capfirst(x), value.split(' '))))

def run():
    try:
        if not Category.objects.exists():
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
            
            print ("Created dummy categories and subcategories")
        else:
            print ("Categories already exist. Aborting.")
    except Exception as e:
        Throw(e)
    else:
        print("Script run successfully")