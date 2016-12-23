from rest_framework.renderers import JSONRenderer

class JSONRootObjectRenderer(JSONRenderer):
    """
        Override the render method of the django rest framework JSONRenderer to allow the following:
        * adding a resource_name root element to all GET requests formatted with JSON
        * reformatting paginated results to the following structure {meta: {}, resource_name: [{},{}]}

        NB: This solution requires a custom pagination serializer and an attribute of 'resource_name'
            defined in the serializer
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {}

        #determine the resource name for this request - default to results if not defined
        view = renderer_context.get('view')
        if hasattr(view, 'get_serializer') and hasattr(view.get_serializer().Meta, 'resource_name'):
            resource_name = view.get_serializer().Meta.resource_name
            response_data[resource_name] = data
        else:
            response_data = data
        #check if the results have been paginated
        # if data.get('paginated_results'):
        #     #add the resource key and copy the results
        #     response_data['meta'] = data.get('meta')
        #     response_data[resource] = data.get('paginated_results')
        # else:
        response = super(JSONRootObjectRenderer, self).render(response_data, accepted_media_type, renderer_context)
        return response