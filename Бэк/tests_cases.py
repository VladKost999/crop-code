import json
from django.urls import reverse
from eqator_projects.models.step import Step
from rest_framework import status

from eqator_projects.models import CasePage, UserProject, UserProjectRole, TestPlan
from eqator_projects.tests.helpers.create_project_mixin import CreateProjectMixin
from helpers.enums import UserProjectRoleEnum


class CaseTestCase(CreateProjectMixin):
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

        UserProject.objects.create(user=self.user_qa, project=self.project, abac_role=qa_role)
        UserProject.objects.create(user=self.user_pm, project=self.project, abac_role=pm_role)
        UserProject.objects.create(user=self.user_dev, project=self.project, abac_role=dev_role)
        UserProject.objects.create(user=self.user_qalead, project=self.project, abac_role=qalead_role)

        another_project_qa = UserProjectRole.objects.filter(project=self.other_project,
                                                            title=self.all_abac_roles[UserProjectRoleEnum.QA][
                                                                'title']).first()
        UserProject.objects.create(user=self.user_other_project, project=self.other_project,
                                   abac_role=another_project_qa)

        self.casepage = CasePage.objects.create(project_id=self.project.id, title="Test_casepage",
                                                priority=CasePage.Priority.LOW)
        self.testplan = TestPlan.objects.create(project=self.project, integration_id=1)
        self.testplan.cases.add(self.casepage)
        self.testplan.save()

    @staticmethod
    def _generate_steps(count):
        """
        Генерирует список шагов.
        """
        steps = []
        for i in range(1, count + 1):
            steps.append({
                "_id": i,
                "description": "",
                "expected_result": "",
                "number": i
            })
        return steps

    def _test_change_status(self, user, new_status, expected_status_code, expected_status, steps=False):
        """
        Вспомогательная функция для лучшей читабельности.
        """
        self._authenticate(user)

        case_page = CasePage.objects.create(
            project_id=self.project.id,
            title="Test_casepage",
            priority=CasePage.Priority.LOW
        )

        if steps:
            Step.objects.bulk_create([Step(case=case_page)])

        url = reverse('cases-change-status', args=(case_page.id,))
        response = self.client.post(url, {'status': new_status})

        self.assertEqual(expected_status_code, response.status_code)
        case_page.refresh_from_db()
        self.assertEqual(case_page.status, expected_status)

    def _test_change_status_patch(self, user, new_status, expected_status_code, expected_status, steps=0):
        """
        Вспомогательная функция для лучшей читабельности.
        """
        self._authenticate(user)
        url = reverse('cases-detail', args=(self.casepage.id,))
        data = {
            "status": new_status,
            "steps": self._generate_steps(steps)
        }
        json_data = json.dumps(data)

        response = self.client.patch(
            url,
            data={
                'data': str(json_data),
                'files_ids': '[]'
            },
        )
        self.assertEqual(expected_status_code, response.status_code)
        self.casepage.refresh_from_db()
        self.assertEqual(self.casepage.status, expected_status)

    def _test_status_post(self, user, new_status, expected_status_code, expected_status, steps=0):
        """
        Вспомогательная функция для лучшей читабельности.
        """
        self._authenticate(user)
        url = reverse('cases-list')
        data = {
            "title": f"test1_{new_status}",
            "status": new_status,
            "project": self.project.pk,
            "steps": self._generate_steps(steps)
        }
        json_data = json.dumps(data)

        response = self.client.post(
            url,
            data={
                'data': str(json_data),
                'files_ids': '[]'
            },
        )
        self.assertEqual(expected_status_code, response.status_code)
        if response.status_code == 201:
            case_page = CasePage.objects.filter(title=f'test1_{new_status}', project=self.project.pk).first()
            self.assertEqual(case_page.status, expected_status)
            return case_page

    def test_change_status_wi_steps(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT),
            (self.user_qalead, 'approved', status.HTTP_200_OK, CasePage.STATUS.APPROVED),
            (self.user_qalead, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT),
            (self.user_qalead, '', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_change_status(user, target_status, expected_status, case_status, True)

    def test_change_status_wo_steps(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'approved', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_change_status(user, target_status, expected_status, case_status, False)

    def test_change_patch(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'approved', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_change_status_patch(user, target_status, expected_status, case_status)

    def test_change_patch_wi_steps(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT),
            (self.user_qalead, 'approved', status.HTTP_200_OK, CasePage.STATUS.APPROVED),
            (self.user_qalead, 'draft', status.HTTP_200_OK, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_change_status_patch(user, target_status, expected_status, case_status, 2)

    def test_post_wi_status_wo_steps(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_201_CREATED, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'approved', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'draft', status.HTTP_201_CREATED, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_400_BAD_REQUEST, CasePage.STATUS.DRAFT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_status_post(user, target_status, expected_status, case_status)

    def test_post_wi_status_wi_steps(self):
        test_cases = [
            (self.user_pm, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_pm, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'draft', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_dev, 'refinement', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'approved', status.HTTP_403_FORBIDDEN, CasePage.STATUS.DRAFT),
            (self.user_qa, 'draft', status.HTTP_201_CREATED, CasePage.STATUS.DRAFT),
            (self.user_qa, 'refinement', status.HTTP_201_CREATED, CasePage.STATUS.REFINEMENT),
            (self.user_qalead, 'approved', status.HTTP_201_CREATED, CasePage.STATUS.APPROVED),
            (self.user_qalead, 'draft', status.HTTP_201_CREATED, CasePage.STATUS.DRAFT),
            (self.user_qalead, 'refinement', status.HTTP_201_CREATED, CasePage.STATUS.REFINEMENT),
        ]
        for user, target_status, expected_status, case_status in test_cases:
            self._test_status_post(user, target_status, expected_status, case_status, 2)

    def test_check_draft_mechanics(self):
        test_cases = [
            (self.user_qalead, 'approved', status.HTTP_200_OK, CasePage.STATUS.APPROVED, 1),
            (self.user_qa, 'approved', status.HTTP_200_OK, CasePage.STATUS.DRAFT, 2),
            (self.user_qalead, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT, 1),
            (self.user_qa, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT, 2),
            (self.user_qalead, 'approved', status.HTTP_200_OK, CasePage.STATUS.APPROVED, 1),
            (self.user_qalead, 'approved', status.HTTP_200_OK, CasePage.STATUS.APPROVED, 2),
            (self.user_qalead, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT, 1),
            (self.user_qa, 'refinement', status.HTTP_200_OK, CasePage.STATUS.REFINEMENT, 2),
        ]
        for user, target_status, expected_status, case_status, steps in test_cases:
            self._test_change_status_patch(user, target_status, expected_status, case_status, steps)

    def test_status_filter(self):
        for case_status in [CasePage.STATUS.REFINEMENT, CasePage.STATUS.DRAFT, CasePage.STATUS.APPROVED]:
            self._test_status_post(self.user_qalead, case_status, status.HTTP_201_CREATED, case_status, 2)

            self._authenticate(self.user_qalead)
            url = reverse('cases-list')
            params = {'status': case_status}
            response = self.client.get(url, params)

            expected_count = CasePage.objects.filter(status=case_status).count()
            actual_count = len(response.json().get('results'))

            self.assertEqual(response.status_code, 200, msg=f'Error with status {case_status}: {response.data}')
            self.assertEqual(expected_count, actual_count, msg=f'Expected {expected_count} results for status {case_status}, got {actual_count}.')

    def test_get_next_prev_others(self):
        self._authenticate(self.user_qalead)

        casepage_alt = CasePage.objects.create(project_id=self.project.id, title="ALT_Test_casepage")

        url = reverse('cases-get-next', args=(self.casepage.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': casepage_alt.id, 'url': '/project_list_slug/-TESTCODE/cases/TESTCODE-C-2', 'title': 'ALT_Test_casepage'})

        url = reverse('cases-get-next', args=(casepage_alt.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': None, 'url': None, 'title': None})

        url = reverse('cases-get-prev', args=(casepage_alt.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': self.casepage.id, 'url': '/project_list_slug/-TESTCODE/cases/TESTCODE-C-1', 'title': 'Test_casepage'})

        url = reverse('cases-get-prev', args=(self.casepage.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': None, 'url': None, 'title': None})

        url = reverse('cases-member-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

        url = reverse('cases-download-files', args=(self.casepage.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['file'])

    def test_clone_case(self):
        self._authenticate(self.user_qalead)
        before = CasePage.objects.count()
        url = reverse('cases-clone', args=(self.casepage.id,))
        response = self.client.post(url)
        after = CasePage.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)
        self.assertTrue(after > before)
