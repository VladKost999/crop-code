

    @extend_schema(parameters=[
        OpenApiParameter(name='q', type=str, description='Search by name'),
        OpenApiParameter(name='stateName',
                         type=str,
                         description='State',
                         enum=[choice[0] for choice in AutoTestRun.TestRunState.choices], required=False)
    ])
    @action(methods=['GET'], detail=True, filterset_class=AutoTestRunFilter, search_fields=['name'])
    def auto_test_runs(self, request, pk, *args, **kwargs):

        queryset = AutoTestRun.objects.filter(project=pk).order_by('-createdDate')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = AutoTestRunSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AutoTestRunSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True, url_path='auto_test_runs/(?P<auto_test_run_pk>[^/.]+)')
    def auto_test_runs_detail(self, request, pk, auto_test_run_pk, *args, **kwargs):
        queryset = AutoTestRun.objects.filter(pk=auto_test_run_pk).first()
        serializer = AutoTestRunDetailSerializer(queryset)
        return Response(serializer.data)

    @extend_schema(parameters=[
        OpenApiParameter(name='q', type=str, description='Search by name'),
        OpenApiParameter(name='outcome',
                         type=str,
                         description='Status',
                         enum=[choice[0] for choice in AutoTestResults.STATUS.choices], required=False)
    ])
    @action(methods=['GET'],
            detail=True,
            url_path='auto_test_runs/(?P<auto_test_run_pk>[^/.]+)/result',
            filterset_class=AutoTestRunResultFilter,
            search_fields=['title', 'autoTestExternalId']
            )
    def auto_test_runs_result(self, request, pk, auto_test_run_pk, *args, **kwargs):
        queryset = AutoTestResults.objects.filter(auto_test_run__pk=auto_test_run_pk)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AutoTestResultsListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AutoTestResultsListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(parameters=[
        OpenApiParameter(name='q', type=str, description='Search by title, externalId'),
        OpenApiParameter(name='status',
                         type=str,
                         description='Status',
                         enum=list(AutoTest.STATUS.values), required=False)
    ],
        responses=AutoTestProjectListSerializer)
    @action(methods=['GET'],
            detail=True,
            filterset_class=AutoTestFilter,
            search_fields=['title', 'externalId'],
            serializer_class=AutoTestProjectListSerializer
            )
    def auto_test(self, request, pk, *args, **kwargs):

        queryset = AutoTest.objects.filter(project_id=pk)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True, url_path='auto_test/(?P<auto_test_pk>[^/.]+)')
    def auto_test_detail(self, request, pk, auto_test_pk, *args, **kwargs):
        from ..serializers.auto_test import AutoTestDetailSrializer
        queryset = AutoTest.objects.filter(pk=auto_test_pk).first()

        serializer = AutoTestDetailSrializer(queryset)
        return Response(serializer.data)
