from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from mock.mock import MagicMock, patch, Mock
from models import DDSEndpoint, DDSUserCredential, Workflow, WorkflowVersion, \
    JobQuestion, JobAnswer, JobStringAnswer, JobDDSFileAnswer, \
    JobAnswerKind, JobDDSOutputDirectoryAnswer, JobInputFile, JobQuestionDataType
from jobfactory import JobFactory, QuestionInfoList, JobFields, \
    JOB_QUESTION_NAME, JOB_QUESTION_PROJECT_NAME, JOB_QUESTION_VM_FLAVOR, JOB_QUESTION_OUTPUT_DIRECTORY
import json


FLY_RNASEQ_URL = "https://raw.githubusercontent.com/Duke-GCB/bespin-cwl/master/packed-workflows/rnaseq-pt1-packed.cwl"


class QuestionInfoListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.cred = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)

    def test_prevent_duplicate_question_keys(self):
        question1 = JobQuestion.objects.create(key="job_order.align_out_prefix",
                                                      name="Output filename prefix",
                                                      data_type=JobQuestionDataType.STRING)
        question2 = JobQuestion.objects.create(key="job_order.align_out_prefix",
                                                      name="Other Output filename prefix",
                                                      data_type=JobQuestionDataType.STRING)

        question_info_list = QuestionInfoList(self.user)
        question_info_list.add_questions([question1, question2])
        errors = question_info_list.get_errors()
        self.assertEqual(2, len(errors))
        self.assertIn({'source': 'job_order.align_out_prefix',
                       'details': 'Setup error: Multiple questions with same key: job_order.align_out_prefix.'}, errors)

    def test_two_different_question_keys(self):
        question1 = JobQuestion.objects.create(key="job_order.align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        question2 = JobQuestion.objects.create(key="job_order.align_out_prefix2",
                                               name="Other Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        question_info_list = QuestionInfoList(self.user)
        question_info_list.add_questions([question1, question2])
        # We have two unanswered questions so we should have two errors
        errors = question_info_list.get_errors()
        self.assertEqual(2, len(errors))
        self.assertIn({'source': 'job_order.align_out_prefix',
                       'details': 'Required field.'}, errors)
        self.assertIn({'source': 'job_order.align_out_prefix2',
                       'details': 'Required field.'}, errors)

    def test_two_different_question_keys_with_user_answers(self):
        question1 = JobQuestion.objects.create(key="job_order.align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='data_')
        question2 = JobQuestion.objects.create(key="job_order.output_index_filename",
                                               name="Output index file",
                                               data_type=JobQuestionDataType.STRING)
        answer2 = JobAnswer.objects.create(question=question2, user=self.user, kind=JobAnswerKind.DDS_FILE)
        JobDDSFileAnswer.objects.create(answer=answer2, project_id='1', file_id='1', dds_user_credentials=self.cred)

        question_info_list = QuestionInfoList(self.user)
        question_info_list.add_questions([question1, question2])
        question_info_list.add_answers([answer1, answer2])
        # We have two unanswered questions so we should have two errors
        errors = question_info_list.get_errors()
        self.assertEqual(0, len(errors))

    def test_answer_without_question(self):
        question1 = JobQuestion.objects.create(key="job_order.align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='data_')
        question_info_list = QuestionInfoList(self.user)
        question_info_list.add_answers([answer1])
        errors = question_info_list.get_errors()
        self.assertEqual(1, len(errors))
        self.assertIn({'source': 'job_order.align_out_prefix',
                       'details': 'Setup error: Answer without question: job_order.align_out_prefix.'}, errors)


class JobFactoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.cred = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=FLY_RNASEQ_URL)

    def add_job_fields(self, job_factory, name, project_name, vm_flavor, project_id, directory_name,
                       dds_user_credentials):
        self.add_string_field(job_factory, JOB_QUESTION_NAME, name)
        self.add_string_field(job_factory, JOB_QUESTION_PROJECT_NAME, project_name)
        self.add_string_field(job_factory, JOB_QUESTION_VM_FLAVOR, vm_flavor)
        question = JobQuestion.objects.create(key=JOB_QUESTION_OUTPUT_DIRECTORY,
                                               name="Directory where results will be saved",
                                               data_type=JobQuestionDataType.DIRECTORY)
        answer = JobAnswer.objects.create(question=question, user=self.user, kind=JobAnswerKind.DDS_OUTPUT_DIRECTORY)
        JobDDSOutputDirectoryAnswer.objects.create(answer=answer, project_id=project_id,
                                                   directory_name=directory_name,
                                                   dds_user_credentials=dds_user_credentials)
        job_factory.add_question(question)
        job_factory.add_answer(answer)

    def add_string_field(self, job_factory, key, value):
        question = JobQuestion.objects.create(key=key, name="Some name", data_type=JobQuestionDataType.STRING)
        answer = JobAnswer.objects.create(question=question, user=self.user, kind=JobAnswerKind.STRING, index=0)
        JobStringAnswer.objects.create(answer=answer, value=value)
        job_factory.add_question(question)
        job_factory.add_answer(answer)

    def test_simple_build_cwl_input(self):
        question1 = JobQuestion.objects.create(key="job_order.threads",
                                               name="Threads to use",
                                               data_type=JobQuestionDataType.INTEGER)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='4')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        question_info_list = job_factory._build_question_info_list()
        job_order = JobFields(question_info_list).job_order
        expected = {
            "threads": 4
        }
        self.assertEqual(expected, json.loads(job_order))

    def test_string_array_build_cwl_input(self):
        question1 = JobQuestion.objects.create(key="job_order.cores",
                                               name="DNA cores to use",
                                               data_type=JobQuestionDataType.STRING,
                                               occurs=2)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=0)
        JobStringAnswer.objects.create(answer=answer1, value='ACGT')
        answer2 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=1)
        JobStringAnswer.objects.create(answer=answer2, value='CCGT')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer2)
        job_factory.add_answer(answer1)
        question_info_list = job_factory._build_question_info_list()
        job_order = JobFields(question_info_list).job_order
        expected = {
            "cores": [
                "ACGT",
                "CCGT"
            ]
        }
        self.assertEqual(expected, json.loads(job_order))

    def test_string_file_build_cwl_input(self):
        question1 = JobQuestion.objects.create(key="job_order.datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=0)
        JobStringAnswer.objects.create(answer=answer1, value='/data/stuff.csv')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        question_info_list = job_factory._build_question_info_list()
        job_order = JobFields(question_info_list).job_order
        expected = {
            "datafile": {
                    "class": "File",
                    "path": "/data/stuff.csv"
            }
        }
        self.assertEqual(expected, json.loads(job_order))

    @patch("data.jobfactory.get_file_name")
    def test_file_build_cwl_input(self, mock_get_file_name):
        mock_get_file_name.return_value = 'stuff.csv'
        question1 = JobQuestion.objects.create(key="job_order.datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.DDS_FILE,
                                           index=0)
        JobDDSFileAnswer.objects.create(answer=answer1, project_id='1', file_id='1', dds_user_credentials=self.cred)
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        question_info_list = job_factory._build_question_info_list()
        job_fields = JobFields(question_info_list)
        expected_filename = '{}_{}'.format(answer1.id, 'stuff.csv')
        expected = {
            "datafile": {
                "class": "File",
                "path": expected_filename
            }
        }
        self.assertEqual(expected, json.loads(job_fields.job_order))

    @patch("data.jobfactory.get_file_name")
    def test_create_simple_job(self, mock_get_file_name):
        mock_get_file_name.return_value = 'stuff.csv'
        question1 = JobQuestion.objects.create(key="job_order.datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.DDS_FILE,
                                           index=0)
        JobDDSFileAnswer.objects.create(answer=answer1, project_id='1', file_id='1', dds_user_credentials=self.cred)
        job_factory = JobFactory(self.user, workflow_version=self.workflow_version)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        self.add_job_fields(job_factory, name="Test project", project_name="myproj",
                            vm_flavor="m1.extrasmall", project_id="1", directory_name="results",
                            dds_user_credentials=self.cred)
        job = job_factory.create_job()
        expected = {
            'datafile': {'path': '1_stuff.csv', 'class': 'File'}
        }
        self.assertEqual(expected, json.loads(job.job_order))
        self.assertEqual("results", job.output_dir.dir_name)
        self.assertEqual("m1.extrasmall", job.vm_flavor)
        job_input_files = JobInputFile.objects.filter(job=job)
        self.assertEqual(1, len(job_input_files))
        self.assertEqual(JobInputFile.DUKE_DS_FILE, job_input_files[0].file_type)
        self.assertEqual(1, len(job_input_files[0].dds_files.all()))
        dds_input_file = job_input_files[0].dds_files.all()[0]
        self.assertEqual("1", dds_input_file.file_id)
        self.assertEqual("1_stuff.csv", dds_input_file.destination_path)
        self.assertEqual(0, dds_input_file.index)

    @patch("data.jobfactory.get_file_name")
    def test_create_job_missing_job_questions(self, mock_get_file_name):
        mock_get_file_name.return_value = 'stuff.csv'
        question1 = JobQuestion.objects.create(key="datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.DDS_FILE,
                                           index=0)
        JobDDSFileAnswer.objects.create(answer=answer1, project_id='1', file_id='1', dds_user_credentials=self.cred)
        job_factory = JobFactory(self.user, workflow_version=self.workflow_version)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        with self.assertRaises(ValidationError) as exception_info:
            job_factory.create_job()
        self.assertIn("Setup error: Missing questions", exception_info.exception.detail[0])
