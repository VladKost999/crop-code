from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from content.serializers.attachment import AttachmentSerializer
from eqator_projects.models import CaseRun, CaseRunStep, CommentStatus, CasePage
from eqator_projects.serializers.tag import TagSerializer
from helpers.enums import CaseStatusEnum, CaseSyncModeEnum
from django.utils.translation import gettext_lazy as _

from user.serializers import UserSerializer
from .milestone import MilestoneReportsShortSerializer


class StepsInfoSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=0)
    status = serializers.ChoiceField(choices=CaseStatusEnum)
    passed = serializers.IntegerField(default=0)
    blocked = serializers.IntegerField(default=0)
    petest = serializers.IntegerField(default=0)
    failed = serializers.IntegerField(default=0)
    untested = serializers.IntegerField(default=0)


class CaseRunsSerializer(serializers.ModelSerializer):
    # code = serializers.CharField(source='case.slug')
    case_id = serializers.IntegerField(source='case.id')
    comments_count = serializers.IntegerField()
    files = AttachmentSerializer(many=True, read_only=True, source='case.attachments')
    issues_count = serializers.IntegerField()
    original_update_by = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = CaseRun
        fields = (
            'id', 'title', 'case_id', 'code', 'priority', 'status', 'behavior', 'absolute_url', 'status_updated_at', 'case_type',
            'comments_count', 'issues_count', 'needs_update', 'original_update_by', 'original_update_at', 'files',
            'tags', 'preconditions', 'requirement', 'description')


class CaseRunsReportsSerializer(CaseRunsSerializer):
    milestone = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(MilestoneReportsShortSerializer())
    def get_milestone(self, obj):
        return MilestoneReportsShortSerializer(obj.run.milestone).data

    class Meta:
        model = CaseRun
        fields = CaseRunsSerializer.Meta.fields + ('milestone',)


class BaseCaseRunsSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='slug')

    class Meta:
        model = CasePage
        fields = (
            'id', 'title', 'code', 'suite', 'priority', 'behavior', 'status', 'absolute_url', 'case_type',
            'preconditions', 'requirement')


class CaseRunPageSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField()
    issues_count = serializers.IntegerField()
    code = serializers.CharField(source='case.slug')
    to_general = serializers.CharField(source='case.absolute_url')
    tags = TagSerializer(many=True)

    class Meta:
        model = CaseRun
        fields = ('id', 'title', 'code', 'priority', 'status', 'behavior', 'preconditions', 'tags', 'to_general', 'case_type',
                  'comments_count', 'issues_count', 'needs_update', 'original_update_by', 'original_update_at',
                  'requirement')


class CaseStepsSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField()
    issues_count = serializers.IntegerField()

    class Meta:
        model = CaseRunStep
        fields = ('id', 'description', 'expected_result', 'status', 'number', 'comments_count', 'issues_count')


class CaseStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRun
        fields = ('status',)


class CommentStatusSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = self.context['instance']

        if instance.status == CommentStatus.CaseStatus.UNTESTED:
            raise ValidationError({'non_field_errors': [_('Нельзя добавить комментарий в статусе "Непроверенный"')]})

        return attrs

    class Meta:
        model = CommentStatus
        fields = ('id', 'status', 'comment', 'created_at')
        extra_kwargs = {
            'comment': {'required': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True}
        }


class CommentStatusChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRun
        fields = ('id', 'status',)
        extra_kwargs = {
            'status': {'required': True}
        }


class CaseSyncSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=CaseSyncModeEnum.choices)


class CaseRunsTestplanSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='case.slug')

    class Meta:
        model = CaseRun
        fields = (
            'id', 'title', 'code', 'priority', 'status',
            'behavior', 'absolute_url', 'case_type', 'needs_update'
        )
