from django.test import TestCase
from bespin_api_v2.jobtemplate import WorkflowVersionConfiguration, JobTemplate, InvalidWorkflowTagException, \
    STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER
from mock import patch, ANY, Mock


class WorkflowVersionConfigurationTestCase(TestCase):
    def test_split_workflow_tag_parts(self):
        self.assertEqual(WorkflowVersionConfiguration.split_workflow_tag_parts("exome/v1/human"), ('exome', 1, 'human'))
        self.assertEqual(WorkflowVersionConfiguration.split_workflow_tag_parts("exome/v2/mouse"), ('exome', 2, 'mouse'))
        for invalid_tag in ["", "exome", "exome/v1/human/other"]:
            with self.assertRaises(InvalidWorkflowTagException):
                WorkflowVersionConfiguration.split_workflow_tag_parts(invalid_tag)

    @patch('bespin_api_v2.jobtemplate.WorkflowVersion')
    @patch('bespin_api_v2.jobtemplate.WorkflowConfiguration')
    def test_constructor(self, mock_workflow_configuration, mock_workflow_version):
        item = WorkflowVersionConfiguration("exome/v1/human")
        mock_workflow_configuration.objects.get.assert_called_with(tag='human', workflow=ANY)
        mock_workflow_version.objects.get.assert_called_with(version=1, workflow__tag='exome')
        self.assertEqual(item.workflow_version, mock_workflow_version.objects.get.return_value)
        self.assertEqual(item.workflow_configuration, mock_workflow_configuration.objects.get.return_value)

    @patch('bespin_api_v2.jobtemplate.WorkflowVersion')
    @patch('bespin_api_v2.jobtemplate.WorkflowConfiguration')
    def test_user_job_fields(self, mock_workflow_configuration, mock_workflow_version):
        item = WorkflowVersionConfiguration("exome/v1/human")
        item.workflow_configuration.system_job_order = {"field1": "A", "field3": "C"}
        item.workflow_version.fields = [
            {"name": "field1"},
            {"name": "field2"},
            {"name": "field3"},
        ]
        self.assertEqual(item.user_job_fields(), [{'name': 'field2'}])


class JobTemplateTestCase(TestCase):
    @patch('bespin_api_v2.jobtemplate.WorkflowVersionConfiguration')
    def test_create_job_order(self, mock_workflow_version_configuration):
        user_fields = [
            {"type": "int", "name": "myint"},
            {"type": "string", "name": "mystr"},
            {"type": {"type": "array",  "items": "int"}, "name": "intary"}
        ]
        job_template = JobTemplate(tag="exome/v1/human", job_order={})
        mock_workflow_version_configuration.return_value.user_job_fields.return_value = user_fields
        job_template.populate_job_order()
        self.assertEqual(job_template.job_order, {
             'intary': [INT_VALUE_PLACEHOLDER], 'myint': INT_VALUE_PLACEHOLDER, 'mystr': STRING_VALUE_PLACEHOLDER
        })

    def test_create_placeholder_value(self):
        job_template = JobTemplate(tag="exome/v1/human", job_order={"A": "B"})
        self.assertEqual(
            job_template.create_placeholder_value(type_name='string', is_array=False),
            STRING_VALUE_PLACEHOLDER)
        self.assertEqual(
            job_template.create_placeholder_value(type_name='int', is_array=False),
            INT_VALUE_PLACEHOLDER)
        self.assertEqual(
            job_template.create_placeholder_value(type_name='int', is_array=True),
            [INT_VALUE_PLACEHOLDER])
        self.assertEqual(
            job_template.create_placeholder_value(type_name='File', is_array=False),
            {
                "class": "File",
                "path": FILE_PLACEHOLDER
            })
        self.assertEqual(
            job_template.create_placeholder_value(type_name='File', is_array=True),
            [{
                "class": "File",
                "path": FILE_PLACEHOLDER
            }])
        self.assertEqual(
            job_template.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=False),
            {
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            })
        self.assertEqual(
            job_template.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=True),
            [{
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            }])

    def test_get_vm_strategy(self):
        mock_workflow_configuration = Mock(default_vm_strategy='good')
        job_order_data = JobTemplate(tag=None, name=None, fund_code=None, stage_group=None, job_order=None,
                                     job_vm_strategy=None)
        self.assertEqual(job_order_data.get_vm_strategy(mock_workflow_configuration), 'good')
        job_order_data = JobTemplate(tag=None, name=None, fund_code=None, stage_group=None, job_order=None,
                                     job_vm_strategy='special')
        self.assertEqual(job_order_data.get_vm_strategy(mock_workflow_configuration), 'special')

    @patch('bespin_api_v2.jobtemplate.JobFactory')
    @patch('bespin_api_v2.jobtemplate.WorkflowVersionConfiguration')
    def test_create_job_factory(self, mock_workflow_version_configuration, mock_job_factory):
        job_template = JobTemplate(tag=None, name=None, fund_code=None, stage_group=None, job_order=None,
                                   job_vm_strategy=None)
        self.assertEqual(job_template.create_job_factory(user=None), mock_job_factory.return_value)
        workflow_version = mock_workflow_version_configuration.return_value.workflow_version
        workflow_configuration = mock_workflow_version_configuration.return_value.workflow_configuration
        mock_job_factory.assert_called_with(None, workflow_version, None, None, None,
                                            workflow_configuration.system_job_order, None,
                                            workflow_configuration.default_vm_strategy,
                                            workflow_configuration.share_group)

    @patch('bespin_api_v2.jobtemplate.JobFactory')
    @patch('bespin_api_v2.jobtemplate.WorkflowVersionConfiguration')
    def test_create_job(self, mock_workflow_version_configuration, mock_job_factory):
        job_template = JobTemplate(tag=None, name=None, fund_code=None, stage_group=None, job_order=None,
                                   job_vm_strategy=None)
        self.assertEqual(job_template.job, None)
        job_template.create_and_populate_job(Mock())
        self.assertEqual(job_template.job, mock_job_factory.return_value.create_job.return_value)
