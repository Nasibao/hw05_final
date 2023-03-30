from django.core.paginator import Paginator

PER_PAGE: int = 10


def get_page_obj(request, obj_list):
    page_number = request.GET.get("page")
    paginator = Paginator(obj_list, PER_PAGE)
    page_obj = paginator.get_page(page_number)
    return page_obj
