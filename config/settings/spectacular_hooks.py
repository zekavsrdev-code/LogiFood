"""
DRF Spectacular hooks for automatic tag assignment based on URL prefixes
"""
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
