from rest_framework import mixins, viewsets


class CreateListViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """Вьюсет, выдающий только список и позволяющий его создавать."""
    pass
