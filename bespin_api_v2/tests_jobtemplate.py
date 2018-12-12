from django.test import TestCase
from bespin_api_v2.jobtemplate import WorkflowVersionConfiguration, JobTemplate, InvalidWorkflowTagException, \
    JobOrderWalker, JobOrderValuesCheck, JobTemplateValidator, InvalidJobTemplateException, \
    STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER
from mock import patch, ANY, Mock, call


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


class JobTemplateValidatorTestCase(TestCase):
    @patch('bespin_api_v2.jobtemplate.JobOrderValuesCheck')
    def test_run_null_required_fields(self, mock_job_order_values_check):
        job_template = Mock()
        job_template.name = None
        job_template.fund_code = None
        job_template.job_order = None
        user_job_fields = Mock()
        validator = JobTemplateValidator()
        with self.assertRaises(InvalidJobTemplateException) as raised_exception:
            validator.run(job_template, user_job_fields)
        self.assertEqual(str(raised_exception.exception), 'Missing required field(s): name, fund_code, job_order')

    @patch('bespin_api_v2.jobtemplate.JobOrderValuesCheck')
    def test_run_with_placeholders(self, mock_job_order_values_check):
        job_template = Mock()
        job_template.name = STRING_VALUE_PLACEHOLDER
        job_template.fund_code = STRING_VALUE_PLACEHOLDER
        job_template.job_order = {
            'threads': 12
        }
        user_job_fields = Mock()
        validator = JobTemplateValidator()
        with self.assertRaises(InvalidJobTemplateException) as raised_exception:
            validator.run(job_template, user_job_fields)
        self.assertEqual(str(raised_exception.exception), 'Missing required field(s): name, fund_code')

    @patch('bespin_api_v2.jobtemplate.JobOrderValuesCheck')
    def test_run(self, mock_job_order_values_check):
        job_template = Mock()
        job_template.name = 'myjob'
        job_template.fund_code = '001'
        job_template.job_order = {
            'threads': 12
        }
        user_job_fields = Mock()
        mock_job_order_values_check.return_value = Mock(keys_requiring_values=[])
        validator = JobTemplateValidator()
        validator.run(job_template, user_job_fields)

    @patch('bespin_api_v2.jobtemplate.JobOrderValuesCheck')
    def test_run_check_job_order_values(self, mock_job_order_values_check):
        job_template = Mock()
        job_template.name = 'myjob'
        job_template.fund_code = '001'
        job_template.job_order = {
            'threads': 12
        }
        user_job_fields = Mock()
        mock_job_order_values_check.return_value = Mock(keys_requiring_values=['badfield'])
        validator = JobTemplateValidator()
        with self.assertRaises(InvalidJobTemplateException) as raised_exception:
            validator.run(job_template, user_job_fields)
        self.assertEqual(str(raised_exception.exception), 'Missing required field(s): badfield')

    def test_is_placeholder_value(self):
        self.assertEqual(JobTemplateValidator.is_placeholder_value("<String Value>"), True)
        self.assertEqual(JobTemplateValidator.is_placeholder_value("<Integer Value>"), True)
        self.assertEqual(JobTemplateValidator.is_placeholder_value("dds://<Project Name>/<File Path>"), True)
        self.assertEqual(JobTemplateValidator.is_placeholder_value("test"), False)
        self.assertEqual(JobTemplateValidator.is_placeholder_value(123), False)


class JobOrderWalkerTestCase(TestCase):
    def test_walk(self):
        walker = JobOrderWalker()
        walker.on_class_value = Mock()
        walker.on_simple_value = Mock()
        walker.walk({
            'color': 'red',
            'weight': 123,
            'file1': {
                'class': 'File',
                'path': 'somepath'
            },
            'file_ary': [
                {
                    'class': 'File',
                    'path': 'somepath1'
                }, {
                    'class': 'File',
                    'path': 'somepath2'
                },
            ],
            'nested': {
                'a': [{
                    'class': 'File',
                    'path': 'somepath3'
                }]
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        })

        walker.on_simple_value.assert_has_calls([
            call('color', 'red'),
            call('weight', 123),
        ])
        walker.on_class_value.assert_has_calls([
            call('file1', {'class': 'File', 'path': 'somepath'}),
            call('file_ary', {'class': 'File', 'path': 'somepath1'}),
            call('file_ary', {'class': 'File', 'path': 'somepath2'}),
            call('nested', {'class': 'File', 'path': 'somepath3'}),
        ])

    def test_format_file_path(self):
        data = [
            # input    expected
            ('https://placeholder.data/stuff/data.txt', 'https://placeholder.data/stuff/data.txt'),
            ('dds://myproject/rawData/SAAAA_R1_001.fastq.gz', 'dds_myproject_rawData_SAAAA_R1_001.fastq.gz'),
            ('dds://project/somepath.txt', 'dds_project_somepath.txt'),
            ('dds://project/dir/somepath.txt', 'dds_project_dir_somepath.txt'),
        ]
        for input_val, expected_val in data:
            self.assertEqual(JobOrderWalker.format_file_path(input_val), expected_val)


class JobOrderValuesCheckTestCase(TestCase):
    def test_walk(self):
        job_order = {
            'good_str': 'a',
            'bad_str': STRING_VALUE_PLACEHOLDER,
            'good_int': 123,
            'bad_int': INT_VALUE_PLACEHOLDER,
            'good_file': {
                'class': 'File',
                'path': 'somepath.txt',
            },
            'bad_file': {
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            },
            'good_str_ary': ['a', 'b', 'c'],
            'bad_str_ary': ['a', STRING_VALUE_PLACEHOLDER, 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'somepath.txt',
            }],
            'bad_file_ary': [{
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'somepath.txt',
                }
            },
            'bad_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': FILE_PLACEHOLDER,
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }
        expected_keys = [
            'job_order.bad_str', 'job_order.bad_int', 'job_order.bad_file', 'job_order.bad_str_ary',
            'job_order.bad_file_ary', 'job_order.bad_file_dict', 'job_order.missing_field',
        ]

        checker = JobOrderValuesCheck(user_job_fields=[{'name': 'missing_field'}])
        checker.walk(job_order)

        self.assertEqual(checker.keys_requiring_values, set(expected_keys))
