from rest_framework import pagination, serializers

class CustomMetaSerializer(serializers.Serializer):
    next_page = pagination.NextPageField(source='*')
    prev_page = pagination.PreviousPageField(source='*')
    record_count = serializers.Field(source='paginator.count')

class CustomPaginationSerializer(pagination.BasePaginationSerializer):
    # Takes the page object as the source
    meta = CustomMetaSerializer(source='*')
    results_field = 'paginated_results'