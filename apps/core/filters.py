"""
Custom filters for the application
"""
from rest_framework import filters


class CustomSearchFilter(filters.SearchFilter):
    """Custom search filter"""
    search_param = 'search'
    search_title = 'Search'
    search_description = 'Search query parameter'
