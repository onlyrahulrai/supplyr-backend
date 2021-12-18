from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict



# This is a pagination function.It is used for the pagination of any Model object.This is build with normal django.
def paginate_func(request,object,page_number,count=4):
    paginator = Paginator(object, count)
    try:
        objects = paginator.page(page_number)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    return objects


class CustomPageNumber(PageNumberPagination):
    '''
    This is a Custom pagination class.It is able to work with any type of model object in api creation.
    '''
    page_size = 2

    def get_paginated_response(self, data):
        return Response(OrderedDict([
             ('totalItems', self.page.paginator.count),
             ('totalPages', self.page.paginator.num_pages),
             ('pageRange', list(self.page.paginator.page_range)),
             ('currentPage', self.page.number),
             ('countItemsOnPage', self.page_size),
             ('start', self.page.start_index()),
             ('end', self.page.end_index()),
             ('next', self.get_next_link()),
             ('previous', self.get_previous_link()),
             ('results', data)
         ]))