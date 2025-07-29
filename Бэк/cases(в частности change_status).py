import json
import django_filters
from django.db.models import Count, Value, F
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from garpix_company.models import get_company_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from ai_assistants.services.action_async import async_action, async_serializer_validate_data
from eqator_projects.models import (
    CasePage, Suite, ProjectPage,
    CasePlan, TestPlan, UserProject, Step
)
from helpers import QSearchFilter
from helpers.enums import BehaviorEnum
from ..permissions import SourcePermission

from ..serializers.case import CaseListSerializer, CaseSerializer, CaseDataSerializer, CaseDetailSerializer, \
    CaseStatusSerializer, \
    CasesOpenAISerializer, CasesOpenAIResultSerializer, CasesOpenAIPreconditionResultSerializer, \
    CasesOpenAIPreconditionSerializer, TestPlanAddSerializer, ListDeleteSerializer, CaseUrlSerializer, \
    CasesOpenAIArrayResultSerializer, CasesOpenAIArraySerializer
from eqator_projects.serializers.test_plan import TestPlanSerializer
from ..services.abac_permissions_service import abac_service
from ..services.notifications import NotifyService
from ..filtersets import SuiteModelMultipleChoiceFilter
from ai_assistants.services.ai_assistant_service import AIAssistantService
from ai_assistants.services.ai_assistant_service import get_response_ai_assistant
from ai_assistants.exceptions import AIAssistantRequestError
from content.models.tags import Tags

Company = get_company_model()


class CasesFilter(FilterSet):
    suite = django_filters.ModelMultipleChoiceFilter(queryset=Suite.objects.all())
    suite_tree = SuiteModelMultipleChoiceFilter(queryset=Suite.objects.all(), field_name='suite')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tags.objects.all())
    priority = django_filters.MultipleChoiceFilter(choices=CasePage.Priority.choices)
    status = django_filters.MultipleChoiceFilter(choices=CasePage.STATUS.choices)
    case_type = django_filters.MultipleChoiceFilter(choices=CasePage.Type.choices)
    behavior = django_filters.MultipleChoiceFilter(choices=BehaviorEnum.choices)
    project = django_filters.ModelChoiceFilter(field_name='project', queryset=ProjectPage.active_on_site.all())
    without_suite = django_filters.BooleanFilter(method='without_suite_filter')
    company = django_filters.ModelChoiceFilter(field_name='project__company', queryset=Company.active_on_site.all())

    def without_suite_filter(self, qs, name, value):
        if value:
            return qs.filter(suite__isnull=True)
        return qs


class CasesView(viewsets.ModelViewSet):
    queryset = CasePage.active_on_site.all().order_by('sort', '-created_at')
    permission_classes = [permissions.IsAuthenticated & SourcePermission]
    filter_backends = [DjangoFilterBackend, QSearchFilter, OrderingFilter]
    filterset_class = CasesFilter
    search_fields = ['title']
    ordering_fields = ['sort']
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']

    def get_permission_source(self):
        if self.action in ['list', 'member_list']:
            return 'cases'
        if self.action == 'approve':
            return 'case_approve'
        if self.action in ['generate_ai_cases_array', 'generate_openai_case', 'get_openai_precondition_text']:
            return 'ai_generation'
        if self.action == 'change_status':
            return None
        return 'case'

    def get_serializer_class(self):
        if self.action in ['list', 'member_list']:
            return CaseListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return CaseDataSerializer
        if self.action == 'generate_openai_case':
            return CasesOpenAISerializer
        if self.action == 'get_openai_precondition_text':
            return CasesOpenAIPreconditionSerializer
        if self.action == 'testplans_add':
            return TestPlanAddSerializer
        if self.action == 'testplans':
            return TestPlanSerializer
        if self.action == 'delete_list':
            return ListDeleteSerializer
        if self.action == 'change_status':
            return CaseStatusSerializer
        if self.action == 'clone':
            return None
        return CaseDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if self.action in {
            self.list.__name__,
            self.member_list.__name__,
        }:
            qs = qs.prefetch_related('tags').select_related('suite').annotate(steps_count=Count('steps'))

        return abac_service.filter_queryset(qs, 'cases', ['project'], self.request.user)

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = request.data.get('data')
        if isinstance(data, str):
            data = json.loads(data)
        new_status = data.get('status', 'draft')
        project = data['project'] if 'project' in data else None
        steps = data['steps'] if 'steps' in data else None
        case_type = data['case_type'] if 'case_type' in data else None
        if case_type != CasePage.Type.TASK and not steps and new_status in [CasePage.STATUS.REFINEMENT,
                                                                            CasePage.STATUS.APPROVED]:
            return Response({'non_field_errors': [_('Отсутствуют шаги')]}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == 'approved':
            user_project = UserProject.objects.filter(project=project, user=request.user).first()
            if not user_project:
                return Response({'result': []}, status=status.HTTP_403_FORBIDDEN)
            if user_project.abac_role.permissions.get('case_approve') != 'full':
                return Response({'result': []}, status=status.HTTP_403_FORBIDDEN)

        instance = self.perform_create(serializer)
        data = CaseSerializer(instance, context={"request": request}).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        data = request.data.get('data')
        if isinstance(data, str):
            data = json.loads(data)
        new_status = data.get('status', 'draft')
        project = data['project'] if 'project' in data else instance.project
        steps = data['steps'] if 'steps' in data else None
        case_type = data['case_type'] if 'case_type' in data else None
        if case_type != CasePage.Type.TASK and not steps and new_status in [CasePage.STATUS.REFINEMENT,
                                                                            CasePage.STATUS.APPROVED]:
            return Response({'non_field_errors': [_('Отсутствуют шаги')]}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == 'approved' and instance.status != 'approved':
            user_project = UserProject.objects.filter(project=project, user=request.user).first()
            if not user_project:
                return Response({'result': []}, status=status.HTTP_403_FORBIDDEN)
            if user_project.abac_role.permissions.get('case_approve') != 'full':
                return Response({'result': []}, status=status.HTTP_403_FORBIDDEN)

        instance = self.perform_update(serializer)
        data = CaseSerializer(instance, context={"request": request}).data
        return Response(data)

    @action(methods=['POST'], detail=True)
    def change_status(self, request, pk, *args, **kwargs):
        instance = self.get_object()

        if 'status' in request.data:
            new_status = request.data.get('status').lower()
        else:
            return Response({'non_field_errors': [_('Отсутствует статус')]}, status=status.HTTP_400_BAD_REQUEST)

        user_project = UserProject.objects.filter(project=instance.project, user=request.user).first()

        status_mapping = {
            'draft': ('case', CasePage.STATUS.DRAFT),
            'approved': ('case_approve', CasePage.STATUS.APPROVED),
            'refinement': ('case', CasePage.STATUS.REFINEMENT),
        }

        if new_status not in status_mapping:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        permission_key, target_status = status_mapping[new_status]
        permissions = user_project.abac_role.permissions.get(permission_key)

        if (new_status == 'approved' and permissions == 'full') or (
                new_status in ['draft', 'refinement'] and permissions in ['full', 'update']):
            new_status = target_status
        else:
            return Response({'result': []}, status=status.HTTP_403_FORBIDDEN)
        if instance.case_type != CasePage.Type.TASK and not Step.objects.filter(
                case=instance).count() and new_status in [CasePage.STATUS.REFINEMENT, CasePage.STATUS.APPROVED]:
            return Response({'non_field_errors': [_('Отсутствуют шаги')]}, status=status.HTTP_400_BAD_REQUEST)

        instance.set_status(new_status)
        NotifyService.notify_casestatus_changed(request=request, instance=instance)
        return Response({'status': 'success'})

    @action(methods=['GET'], detail=False)
    def member_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses=CasesOpenAIResultSerializer, request=CasesOpenAISerializer)
    @async_action(methods=['POST'], detail=False, filterset_class=None, search_fields=None)
    async def generate_openai_case(self, request, *args, **kwargs):

        serializer = await async_serializer_validate_data(self.get_serializer, data=request.data)
        try:
            data = await get_response_ai_assistant(**serializer.validated_data, user=request.user)
            response_data = data.get('response')
            data = self.__check_debug_mode(request, response_data, data.get('debug'))

        except AIAssistantRequestError as exc:
            return Response({'non_field_errors': exc.__str__()}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)

    def __check_debug_mode(self, request, data_dict, debug_message):
        is_debug = request.query_params.get('debug', '').lower() in ("yes", "true", "t", "1")
        if is_debug:
            data_dict.update({'debug': debug_message})
        return data_dict

    @extend_schema(responses=CasesOpenAIArrayResultSerializer, request=CasesOpenAIArraySerializer)
    @async_action(methods=['POST'], detail=False, filterset_class=None, search_fields=None)
    async def generate_ai_cases_array(self, request, *args, **kwargs):
        serializer = await async_serializer_validate_data(CasesOpenAIArraySerializer, data=request.data)
        suite = serializer.validated_data.pop('suite', None)
        try:
            data = await get_response_ai_assistant(
                **serializer.validated_data,
                is_array=True,
                user=request.user
            )
        except AIAssistantRequestError as exc:
            serializer = await async_serializer_validate_data(CasesOpenAIArrayResultSerializer,
                                                              data={
                                                                  "success": False,
                                                                  "cases_count": 0,
                                                                  "error": str(exc),
                                                              })
            return Response(data=serializer.data, status=status.HTTP_400_BAD_REQUEST)
        await CasePage.create_cases_from_ai(
            data=data.get('response'),
            user=request.user,
            case_type=serializer.validated_data['case_type'],
            project=serializer.validated_data['project'],
            suite=suite
        )
        data_dict = self.__check_debug_mode(request, {"success": True, "cases_count": len(data.get('response'))},
                                            debug_message=data.get('debug'))

        serializer = CasesOpenAIArrayResultSerializer(data_dict)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=CasesOpenAIPreconditionResultSerializer, request=CasesOpenAIPreconditionSerializer)
    @action(methods=['POST'], detail=False, filterset_class=None, search_fields=None)
    def get_openai_precondition_text(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = AIAssistantService.generate_prompt(
            ai_assistant=serializer.validated_data['project'].ai_assistant,
            message='{text}',
            project_description=serializer.validated_data['project'].description,
            case_type=serializer.validated_data['case_type'],
        )

        return Response(data)

    @action(methods=['GET'], detail=True)
    def get_next(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        cases = self.get_queryset().filter(
            project=instance.project, id__gt=instance.id, suite=instance.suite
        ).order_by('sort')
        if cases.count() == 0:
            next_suite = Suite.get_next(instance.suite, instance.project)
            if next_suite:
                cases = self.get_queryset().filter(project=instance.project, suite=next_suite).order_by('sort')
        if cases.count() > 0:
            next_case = cases.first()
            data = {"id": next_case.id,
                    "url": next_case.absolute_url,
                    "title": next_case.title}
        else:
            data = {"id": None,
                    "url": None,
                    "title": None}
        return Response(data)

    @action(methods=['GET'], detail=True)
    def get_prev(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        cases = self.get_queryset().filter(
            project=instance.project, id__lt=instance.id, suite=instance.suite
        ).order_by('sort', 'id')

        if cases.count() == 0:
            prev_suite = Suite.get_prev(instance.suite, instance.project)
            if prev_suite:
                cases = self.get_queryset().filter(project=instance.project, suite=prev_suite).order_by('sort', 'id')

        if cases.count() > 0:
            prev_case = cases.last()
            data = {"id": prev_case.id,
                    "url": prev_case.absolute_url,
                    "title": prev_case.title}
        else:
            data = {"id": None,
                    "url": None,
                    "title": None}
        return Response(data)

    @action(methods=['GET'], detail=True)
    def testplans(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = TestPlan.objects.filter(
            cases__id__exact=instance.pk)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['POST'], detail=True)
    def testplans_add(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        _data = {'added': [], 'skipped': []}
        for testplan_pk in serializer.validated_data['testplans']:
            results = TestPlan.objects.filter(id=testplan_pk)
            if results.exists():
                testplan = results.first()
                CasePlan.objects.get_or_create(case=instance, plan=testplan)
                _data['added'].append(testplan_pk)
            else:
                _data['skipped'].append(testplan_pk)
        return Response(_data)

    @extend_schema(parameters=[
        OpenApiParameter(name='full_list', type=bool)
    ])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).annotate(show_link=Value(
            abac_service.check_project_permissions(
                UserProject.active_objects.filter(project=F('project'), user=request.user).first(), 'case',
                request.method)
        )
        )
        if request.GET.get('full_list', None) is not None:
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'next': None,
                'previous': None,
                'results': serializer.data
            })
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['POST'], detail=False)
    def delete_list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get('ids', [])
        deleted = CasePage.objects.filter(id__in=ids).delete()
        num = deleted[1].get('eqator_projects.CasePage')
        return Response({'deleted': num if num else 0})

    @extend_schema(responses=[CaseUrlSerializer])
    @action(methods=['post'], detail=True, filterset_class=None)
    def clone(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        return Response(CaseUrlSerializer(instance.clone_object()).data)

    @action(methods=['get'], detail=True)
    def download_files(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        from eqator_projects.services.zip_archive import zip_nonproject
        file_path = zip_nonproject(instance, pk, 'case')
        return Response({"file": request.build_absolute_uri(file_path)})
