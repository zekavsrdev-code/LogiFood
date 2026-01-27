"""
OpenAPI schema helpers. Build parameters from FilterSet classes so Swagger
shows filter query params without hand-coding @extend_schema(parameters=...).
"""
import django_filters
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes


def openapi_parameters_from_filterset(filterset_class):
    """
    Build a list of OpenApiParameter from a FilterSet's base_filters.
    Uses each filter's type, required, choices (when applicable), and help_text.
    """
    if not filterset_class or not hasattr(filterset_class, "base_filters"):
        return []

    params = []
    for name, f in filterset_class.base_filters.items():
        extra = getattr(f, "extra", None) or {}
        required = getattr(f, "required", extra.get("required", False))
        description = extra.get("help_text") or getattr(f, "label", "") or ""

        if isinstance(f, django_filters.ChoiceFilter):
            choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
            enum = [c[0] for c in choices] if choices else None
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.STR,
                    enum=enum,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, django_filters.TypedChoiceFilter):
            choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
            enum = [c[0] for c in choices] if choices else None
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.STR,
                    enum=enum,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, django_filters.MultipleChoiceFilter):
            choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
            enum = [c[0] for c in choices] if choices else None
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.STR,
                    enum=enum,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, django_filters.CharFilter):
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.STR,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, django_filters.NumberFilter):
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.NUMBER,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, django_filters.BooleanFilter):
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.BOOL,
                    required=required,
                    description=description or None,
                )
            )
        elif isinstance(f, (django_filters.DateFilter, django_filters.DateTimeFilter)):
            api_type = OpenApiTypes.DATE if isinstance(f, django_filters.DateFilter) else OpenApiTypes.DATETIME
            params.append(
                OpenApiParameter(
                    name,
                    type=api_type,
                    required=required,
                    description=description or None,
                )
            )
        else:
            params.append(
                OpenApiParameter(
                    name,
                    type=OpenApiTypes.STR,
                    required=required,
                    description=description or None,
                )
            )
    return params
