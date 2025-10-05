from rest_framework.pagination import PageNumberPagination


class OfferListPagination:
    """
    Custom pagination class for offer listings.

    - Defaults to 6 items per page.
    - Allows clients to adjust page size via the `page_size` query parameter (max: 100).
    - Uses DRF’s PageNumberPagination internally.
    """
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginator.page_size_query_param = self.page_size_query_param
        paginator.max_page_size = self.max_page_size
        self.paginator = paginator
        return paginator.paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)
