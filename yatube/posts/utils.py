from django.core.paginator import Paginator

POST_VIEW = 10


def post_listing(posts, request):
    """Пажинатор сайта"""
    paginator = Paginator(posts, POST_VIEW)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
