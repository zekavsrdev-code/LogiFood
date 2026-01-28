"""
OpenAPI schema helpers. Build parameters from FilterSet classes so Swagger
shows filter query params without hand-coding @extend_schema(parameters=...).
"""
from typing import Optional, Sequence
import django_filters
from django.db.utils import DatabaseError
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes


def _enum_value(v):
    """Normalize choice value to JSON-serializable (handles ModelChoiceIteratorValue, Enum)."""
    if v is None:
        return None
    for _ in range(5):  # avoid infinite loop on weird choices
        if not hasattr(v, "value") or isinstance(v, (str, int, float, bool)):
            break
        v = getattr(v, "value", v)
    if isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def _choices_to_enum(choices):
    """Return list of enum values from filter choices, or None if DB not ready (e.g. before migrate)."""
    if not choices:
        return None
    try:
        return [_enum_value(c[0]) for c in choices]
    except DatabaseError:
        return None


def request_has_list_params(request, filterset_class, extra_param_names: Optional[Sequence[str]] = None) -> bool:
    """
    Return True if request has any query params that affect list result
    (filterset fields + optional extra names like 'ordering').
    Use to decide cache vs full filter path without duplicating param lists.
    """
    if getattr(request, "query_params", None) is None:
        return False
    qp = request.query_params
    if filterset_class and hasattr(filterset_class, "base_filters"):
        for name in filterset_class.base_filters:
            if qp.get(name) not in (None, ""):
                return True
    for name in extra_param_names or []:
        if qp.get(name) not in (None, ""):
            return True
    return False


def openapi_parameters_from_filterset(
    filterset_class,
    ordering_fields: Optional[Sequence[str]] = None,
):
    """
    Build a list of OpenApiParameter from a FilterSet's base_filters.
    Optionally append an 'ordering' param when ordering_fields is given.
    On DB errors (e.g. tables missing at migrate time), returns only ordering param.
    """
    if not filterset_class or not hasattr(filterset_class, "base_filters"):
        params = []
    else:
        try:
            params = _filterset_to_openapi_params(filterset_class)
        except DatabaseError:
            params = []
    if ordering_fields:
        params.append(
            OpenApiParameter(
                "ordering",
                type=OpenApiTypes.STR,
                required=False,
                description="Sort by: " + ", ".join(ordering_fields) + " (prefix with - for descending)",
            )
        )
    return params


def _field_uses_queryset(f):
    """True if filter field uses a model queryset (would hit DB when iterating choices)."""
    field = getattr(f, "field", None)
    return field is not None and getattr(field, "queryset", None) is not None


def _filterset_to_openapi_params(filterset_class):
    """Build OpenApiParameter list from filterset base_filters."""
    params = []
    for name, f in getattr(filterset_class, "base_filters", {}).items():
        extra = getattr(f, "extra", None) or {}
        required = getattr(f, "required", extra.get("required", False))
        description = extra.get("help_text") or getattr(f, "label", "") or ""

        if isinstance(f, django_filters.ChoiceFilter):
            # Never iterate choices for model-backed filters (avoids DB at import/migrate time).
            if _field_uses_queryset(f):
                enum = None
            else:
                choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
                enum = _choices_to_enum(choices)
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
            if _field_uses_queryset(f):
                enum = None
            else:
                choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
                enum = _choices_to_enum(choices)
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
            if _field_uses_queryset(f):
                enum = None
            else:
                choices = getattr(f.field, "choices", None) or extra.get("choices") or ()
                enum = _choices_to_enum(choices)
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
