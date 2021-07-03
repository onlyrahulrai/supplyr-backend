from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate_func(request,object,page_number,count=4):
    print(page_number)
    
    paginator = Paginator(object, count)
    try:
        objects = paginator.page(page_number)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    return objects