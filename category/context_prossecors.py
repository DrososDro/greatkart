from .models import Category


def menu_links(request):
    links = Category.objects.all()
    # this return a dict with the str method
    return dict(links=links)
