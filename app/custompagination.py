from rest_framework.pagination import LimitOffsetPagination
class LimitOffsetPaginationUpperBound(LimitOffsetPagination):
    max_limit=8