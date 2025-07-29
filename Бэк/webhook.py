from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from garpix_page.models import BasePage
from garpix_utils.models import DeleteMixin

from eqator_projects.mixins.sidebarpage_context_mixin import SidebarPageContextMixin
from eqator_projects.models import ProjectPage
from eqator_projects.models.auto_test_runs import AutoTestRun


class WebhookPage(BasePage, DeleteMixin, SidebarPageContextMixin):
    class TypeRequest(models.TextChoices):
        POST = 'post', 'post'
        PUT = 'put', 'put'
        DELETE = 'delete', 'delete'

    description = models.TextField(verbose_name=_('Описание'), blank=True, default='')

    webhook_url = models.URLField(verbose_name=_('URL Вебхука'), blank=True, null=True, default='')
    webhook_settings = models.JSONField(verbose_name=_('Параметры URL'), blank=True, null=True)
    webhook_headers = models.JSONField(verbose_name=_('Заголовки HTTP'), blank=True, null=True)
    webhook_body = models.JSONField(verbose_name=_('Тело HTTP'), blank=True, null=True)

    type_request = models.CharField(verbose_name='Тип запроса', choices=TypeRequest.choices, default=TypeRequest.POST,
                                    max_length=75, blank=True)
    project: ProjectPage = models.ForeignKey(ProjectPage, verbose_name=_('Проект'),
                                             on_delete=models.CASCADE,
                                             related_name='project_webhooks',
                                             blank=True,
                                             null=True)
    auto_test_runs = models.ForeignKey(AutoTestRun, verbose_name=_('Прогон'),
                                       on_delete=models.CASCADE,
                                       related_name='auto_test_run_webhooks',
                                       blank=True,
                                       null=True)

    def get_context(self, request=None, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)
        context.update(self.get_sidebar(self.project, request))
        return context

    @property
    def absolute_url(self):
        language_prefix = translation.get_language()
        if language_prefix == settings.LANGUAGE_CODE:
            return self.url
        return language_prefix + self.url

    def set_url(self, parent=None):
        parent = parent or self.project

        self.url = ''

        if parent and parent.url != '/':
            self.url = parent.url

        if self.slug:
            self.url += f"/webhook/{self.slug}"

    class Meta:
        verbose_name = 'Вебхук'
        verbose_name_plural = 'Вебхуки'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if (not self.title_ru) and (self.title_en):
            self.title_ru = self.title_en
        super().save(*args, **kwargs)
