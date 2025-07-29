import json

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import status

from content.models.tags import Tags
from eqator_projects.models import RunPage, CasePage, UserProject, UserProjectRole, MilestonePage, CaseRun
from eqator_projects.tests.helpers.create_project_mixin import CreateProjectMixin
from helpers.enums import UserProjectRoleEnum


class RunsViewTestCase(CreateProjectMixin):
    def setUp(self) -> None:
        self._set_common_data()
        self.project = self._create_project(self.project_data)
        self.project.sites.set(self.sites)
        self.other_project = self._create_project(self.project2_data)
        self.other_project.sites.set(self.sites)

        user_project_roles = UserProjectRole.objects.filter(project=self.project)
        qalead_role = user_project_roles.filter(
            title=self.all_abac_roles[UserProjectRoleEnum.QALEAD]['title']).first()
        pm_role = user_project_roles.filter(title=self.all_abac_roles[UserProjectRoleEnum.PM]['title']).first()
        qa_role = user_project_roles.filter(title=self.all_abac_roles[UserProjectRoleEnum.QA]['title']).first()
        dev_role = user_project_roles.filter(title=self.all_abac_roles[UserProjectRoleEnum.DEV]['title']).first()

        self.up_qa = UserProject.objects.create(user=self.user_qa, project=self.project, abac_role=qa_role)
        self.up_pm = UserProject.objects.create(user=self.user_pm, project=self.project, abac_role=pm_role)
        self.up_dev = UserProject.objects.create(user=self.user_dev, project=self.project, abac_role=dev_role)
        self.up_qalead = UserProject.objects.create(user=self.user_qalead, project=self.project, abac_role=qalead_role)

        another_project_qa = UserProjectRole.objects.filter(project=self.other_project,
                                                            title=self.all_abac_roles[UserProjectRoleEnum.QA][
                                                                'title']).first()
        UserProject.objects.create(user=self.user_other_project, project=self.other_project,
                                   abac_role=another_project_qa)

        self.tag = Tags.objects.create(title='Test Tag 1')
        self.casepage = CasePage.objects.create(project_id=self.project.id, title="Test",
                                                priority=CasePage.Priority.LOW, status=CasePage.STATUS.APPROVED)
        self.casepage.tags.add(self.tag)
        self.milestone = MilestonePage.objects.create(project=self.project, title="Test Milestone")
        self.runpage = RunPage.objects.create(project=self.project, title="Test Run", milestone=self.milestone, assigned_to=self.up_dev)
        self.case_run = CaseRun.objects.create(run=self.runpage, case=self.casepage, status=CaseRun.CaseStatus.UNTESTED)

    def test_create_run(self):
        self._authenticate(self.user_qalead)
        url = reverse('runs-list')
        data = {
            "data": {
                "title": "string",
                "references": "string",
                "description": "string",
                "project": self.project.pk,
                "cases": [
                    self.casepage.pk
                ],
                "case_ordering": "ASC"
            }
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RunPage.objects.count(), 2)

    def test_update_run(self):
        self._authenticate(self.user_qalead)

        url = reverse('runs-detail', args=[self.runpage.id])
        updated_data = {
            "title": "Updated Run title",
            "references": "Updated Run references",
            "description": "Updated Run description",
        }

        response = self.client.patch(url, data=json.dumps({"data": updated_data}), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset(updated_data, response.json())

        self.runpage.refresh_from_db()
        for key, value in updated_data.items():
            self.assertEqual(getattr(self.runpage, key), value)

    def test_assign_run(self):
        self._authenticate(self.user_qalead)
        url = reverse('runs-assigned', args=[self.runpage.id])
        data = {
            "deadline": (timezone.now() + timezone.timedelta(hours=24)).isoformat(),
            "user_project": self.up_qa.id,
            "description": "test911"
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.runpage.refresh_from_db()
        self.assertEqual(self.runpage.assigned_to, self.up_qa)

    def test_set_run_in_process(self):
        self._authenticate(self.user_qalead)
        url = reverse('runs-in-process', args=[self.runpage.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.runpage.refresh_from_db()
        self.assertEqual(self.runpage.status, RunPage.RunPlanStatus.INPROCESS)

    def test_set_run_completed(self):
        self._authenticate(self.user_qalead)
        url = reverse('runs-completed', args=[self.runpage.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.runpage.refresh_from_db()
        self.assertEqual(self.runpage.status, RunPage.RunPlanStatus.COMPLETED)

    def test_get_steps_info(self):
        self._authenticate(self.user_qa)
        url = reverse('runs-steps-info')
        models = {'case': self.case_run.id, 'run': self.runpage.id, 'milestone': self.milestone.id}
        for key, item in models.items():
            params = {
                'id': item,
                'model': key
            }
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=key)
            self.assertEqual(response.json(), {"non_field_errors": [_("Не указан параметр 'model'")]}, msg=key)
            response = self.client.get(url, {'model': key})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=key)
            self.assertEqual(response.json(), {"non_field_errors": [_("Не указан параметр 'id'")]}, msg=key)
            response = self.client.get(url, params)
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=key)
            response = self.client.get(url, {'model': key, 'id': 999})
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=key)
            response = self.client.get(url, {'model': 'test', 'id': 999})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=key)
            self.assertEqual(response.json(), {"non_field_errors": [_("Недопустимый параметр 'model'. Доступны ['run', 'case', 'milestone']")]}, msg=key)

    def test_get_cases(self):
        self._authenticate(self.user_qa)
        url = reverse('runs-cases', args=[self.runpage.id])
        params = {
            'id': self.case_run.id,
            'tags': [self.tag.id],
            'priority': CasePage.Priority.LOW,
            'status': CaseRun.CaseStatus.UNTESTED,
            'q': 'Test',
            'without_suite': True
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 1)

    def test_get_run_case_detail(self):
        self._authenticate(self.user_qa)
        url = reverse('runs-case-detail', args=[self.runpage.id, self.case_run.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], self.case_run.id)

    def test_change_case_status(self):
        self._authenticate(self.user_qa)
        url = reverse('runs-case-steps-change-status', args=[self.runpage.id, self.case_run.id])
        data = {
            "status": CaseRun.CaseStatus.PASSED
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.case_run.refresh_from_db()
        self.assertEqual(self.case_run.status, CaseRun.CaseStatus.PASSED)

    def test_generate_cases_excel(self):
        self._authenticate(self.user_qalead)
        url = reverse('runs-generate-cases-excel', args=[self.runpage.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
