"""
DRF Spectacular hooks for automatic tag assignment and schema sanitization.
"""


def _make_schema_json_serializable(obj):
    """Recursively replace ModelChoiceIteratorValue so schema can be JSON-serialized."""
    try:
        from django.forms.models import ModelChoiceIteratorValue
    except ImportError:
        ModelChoiceIteratorValue = type("_Never", (), {})  # no instances

    if isinstance(obj, dict):
        return {k: _make_schema_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_schema_json_serializable(v) for v in obj]
    if isinstance(obj, ModelChoiceIteratorValue):
        return _make_schema_json_serializable(obj.value)
    return obj


def postprocess_schema_serializable(result, generator, request, public):
    """Ensure schema contains only JSON-serializable values (fixes ModelChoiceIteratorValue)."""
    return _make_schema_json_serializable(result)


def postprocess_tags(result, generator, request, public):
    """
    Automatically assign tags based on URL path prefixes
    This hook runs after the schema is generated
    """
    # Map URL prefixes to tags (order matters - more specific first)
    url_tag_map = [
        ('/api/auth/', 'Authentication'),
        ('/api/products/', 'Products'),
        ('/api/orders/', 'Orders'),
        ('/api/', 'Core'),  # Default for other /api/ endpoints
    ]
    
    # Process all paths in the schema
    if 'paths' in result:
        for path, methods in result['paths'].items():
            # Find matching tag based on path prefix
            tag = None
            for prefix, tag_name in url_tag_map:
                if path.startswith(prefix):
                    tag = tag_name
                    break
            
            # If no tag found, use 'Core' as default
            if not tag:
                tag = 'Core'
            
            # Apply tag to all operations in this path
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    # Replace existing tags with our tag
                    operation['tags'] = [tag]
    
    return result
