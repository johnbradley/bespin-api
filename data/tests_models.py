from django.test import TestCase
from models import DDSEndpoint, DDSUserCredential
from models import Workflow, WorkflowVersion
from models import Job, JobInputFile, DDSJobInputFile, URLJobInputFile, JobOutputDir, JobError
from models import LandoConnection
from models import JobQuestionnaire, JobQuestion, JobAnswerSet, JobAnswer, JobStringAnswer, JobDDSFileAnswer
from models import JobQuestionDataType
from django.db import IntegrityError
from django.contrib.auth.models import User


CWL_URL = 'https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl'


class DDSEndpointTests(TestCase):
    # Not validating blank or null fields here, as it does not happen at the model layer
    # It is the responsibility of a form or serializer to do that.

    def test_unique_parameters1(self):
        endpoint1 = DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        self.assertIsNotNone(endpoint1)
        endpoint2 = DDSEndpoint.objects.create(name='endpoint2', agent_key='def456')
        self.assertIsNotNone(endpoint2)
        self.assertNotEqual(endpoint1, endpoint2)
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint3', agent_key=endpoint1.agent_key)

    def test_unique_parameters2(self):
        DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint1', agent_key='ghi789')


class DDSUserCredentialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.endpoint2 = DDSEndpoint.objects.create(name='app2', agent_key='abc124')

    def test_unique_parameters1(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=self.user, token='def456', endpoint=self.endpoint)

    def test_unique_parameters2(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        other_user = User.objects.create_user('other_user')
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=other_user, token='abc123', endpoint=self.endpoint)

    def test_user_can_have_creds_for_diff_endpoints(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint, dds_id='1')
        DDSUserCredential.objects.create(user=self.user, token='abc124', endpoint=self.endpoint2, dds_id='2')


class WorkflowTests(TestCase):
    def test_basic_functionality(self):
        Workflow.objects.create(name='RnaSeq')
        workflow = Workflow.objects.first()
        self.assertEqual('RnaSeq', workflow.name)


class WorkflowVersionTests(TestCase):
    def setUp(self):
        self.workflow = Workflow.objects.create(name='RnaSeq')

    def test_basic_functionality(self):
        WorkflowVersion.objects.create(workflow=self.workflow,
                                       object_name='#main',
                                       version='1',
                                       url=CWL_URL)
        workflow_version = WorkflowVersion.objects.first()
        self.assertEqual(self.workflow, workflow_version.workflow)
        self.assertEqual('#main', workflow_version.object_name)
        self.assertEqual(1, workflow_version.version)
        self.assertEqual(CWL_URL, workflow_version.url)
        self.assertIsNotNone(workflow_version.created)

    def test_default_object_name(self):
        WorkflowVersion.objects.create(workflow=self.workflow,
                                       version='1',
                                       url=CWL_URL)
        workflow_version = WorkflowVersion.objects.first()
        self.assertEqual('#main', workflow_version.object_name)

    def test_create_with_description(self):
        desc = """This is a detailed description of the job."""
        WorkflowVersion.objects.create(workflow=self.workflow, description=desc, version=1)
        wv = WorkflowVersion.objects.first()
        self.assertEqual(desc, wv.description)

    def test_version_num_and_workflow_are_unique(self):
        WorkflowVersion.objects.create(workflow=self.workflow, description="one", version=1)
        with self.assertRaises(IntegrityError):
            WorkflowVersion.objects.create(workflow=self.workflow, description="two", version=1)

    def test_sorted_by_version_num(self):
        WorkflowVersion.objects.create(workflow=self.workflow, description="two", version=2)
        a_workflow_version = WorkflowVersion.objects.create(workflow=self.workflow, description="one", version=1)
        WorkflowVersion.objects.create(workflow=self.workflow, description="three", version=3)
        versions = [wv.version for wv in WorkflowVersion.objects.all()]
        self.assertEqual([1, 2, 3], versions)
        a_workflow_version.version = 4
        a_workflow_version.save()
        versions = [wv.version for wv in WorkflowVersion.objects.all()]
        self.assertEqual([2, 3, 4], versions)


class JobTests(TestCase):
    def setUp(self):
        workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)
        self.user = User.objects.create_user('test_user')
        self.sample_json = "{'type': 1}"

    def test_create(self):
        Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                           vm_project_name='jpb67',
                           job_order=self.sample_json)
        job = Job.objects.first()
        self.assertEqual(self.workflow_version, job.workflow_version)
        self.assertEqual(self.user, job.user)
        self.assertIsNotNone(job.created)
        self.assertEqual(Job.JOB_STATE_NEW, job.state)
        self.assertIsNotNone(job.last_updated)
        self.assertIsNotNone(job.vm_flavor)
        self.assertEqual(None, job.vm_instance_name)
        self.assertEqual('jpb67', job.vm_project_name)

    def test_create_with_name(self):
        Job.objects.create(name='Rna Seq for B-Lab', user=self.user)
        job = Job.objects.first()
        self.assertEqual('Rna Seq for B-Lab', job.name)

    def test_state_changes(self):
        # Create job which should start in new state
        Job.objects.create(workflow_version=self.workflow_version, user=self.user, job_order=self.sample_json)
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_NEW, job.state)

        # Set state to create VM
        job.state = Job.JOB_STATE_RUNNING
        job_created = job.created
        job_updated = job.last_updated
        job.save()
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_RUNNING, job.state)
        # last_updated should have changed
        self.assertEqual(job_created, job.created)
        self.assertLess(job_updated, job.last_updated)

        # Set state to canceled
        job.state = Job.JOB_STATE_CANCEL
        job.save()
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_CANCEL, job.state)

    @staticmethod
    def add_job_fields(obj):
        obj.user = User.objects.create_user('test_user')
        obj.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        obj.user_credentials = DDSUserCredential.objects.create(user=obj.user, token='abc123', endpoint=obj.endpoint)
        workflow = Workflow.objects.create(name='RnaSeq')
        obj.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)
        obj.sample_json = "{'type': 1}"
        obj.job = Job.objects.create(workflow_version=obj.workflow_version, user=obj.user,
                                     job_order=obj.sample_json)

    def test_sorted_by_created(self):
        j1 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j2 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j3 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j4 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        job_ids = [job.id for job in Job.objects.all()]
        self.assertEqual([j1.id, j2.id, j3.id, j4.id], job_ids)
        j2.delete()
        j2 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        job_ids = [job.id for job in Job.objects.all()]
        self.assertEqual([j1.id, j3.id, j4.id, j2.id], job_ids)


class JobInputFileTests(TestCase):
    def setUp(self):
        JobTests.add_job_fields(self)

    def test_dds_file(self):
        job_input_file = JobInputFile.objects.create(job=self.job,
                                                     file_type=JobInputFile.DUKE_DS_FILE,
                                                     workflow_name='seq')
        DDSJobInputFile.objects.create(job_input_file=job_input_file,
                                       project_id='1234',
                                       file_id='5321',
                                       dds_user_credentials=self.user_credentials,
                                       destination_path='sample.fasta',
                                       index=1)
        # Test job fields
        job_input_file = JobInputFile.objects.first()
        self.assertEqual(self.job, job_input_file.job)
        self.assertEqual(JobInputFile.DUKE_DS_FILE, job_input_file.file_type)
        self.assertEqual('seq', job_input_file.workflow_name)

        # Test dds_files
        dds_files = job_input_file.dds_files.all()
        self.assertEqual(1, len(dds_files))
        dds_file = dds_files[0]
        self.assertEqual(job_input_file, dds_file.job_input_file)
        self.assertEqual('1234', dds_file.project_id)
        self.assertEqual(self.user_credentials, dds_file.dds_user_credentials)
        self.assertEqual('sample.fasta', dds_file.destination_path)
        self.assertEqual(1, dds_file.index)

    def test_dds_file_array(self):
        job_input_file = JobInputFile.objects.create(job=self.job,
                                                     file_type=JobInputFile.DUKE_DS_FILE_ARRAY,
                                                     workflow_name='seq')
        DDSJobInputFile.objects.create(job_input_file=job_input_file,
                                       project_id='1234',
                                       file_id='5321',
                                       dds_user_credentials=self.user_credentials,
                                       destination_path='sample1.fasta',
                                       index=1)

        DDSJobInputFile.objects.create(job_input_file=job_input_file,
                                       project_id='1234',
                                       file_id='5322',
                                       dds_user_credentials=self.user_credentials,
                                       destination_path='sample2.fasta',
                                       index=2)

        job_input_file = JobInputFile.objects.first()
        self.assertEqual(self.job, job_input_file.job)
        self.assertEqual(JobInputFile.DUKE_DS_FILE_ARRAY, job_input_file.file_type)
        self.assertEqual('seq', job_input_file.workflow_name)
        dds_files = job_input_file.dds_files.all()
        self.assertEqual(2, len(dds_files))
        self.assertIn('5321', [dds_file.file_id for dds_file in dds_files])
        self.assertIn('5322', [dds_file.file_id for dds_file in dds_files])

    def test_url_file(self):
        job_input_file = JobInputFile.objects.create(job=self.job,
                                                     file_type=JobInputFile.URL_FILE,
                                                     workflow_name='myseq')
        URLJobInputFile.objects.create(job_input_file=job_input_file,
                                       url='https://data.org/sample.fasta',
                                       destination_path='sample.fasta',
                                       index=1)

        # Test job fields
        job_input_file = JobInputFile.objects.first()
        self.assertEqual(self.job, job_input_file.job)
        self.assertEqual(JobInputFile.URL_FILE, job_input_file.file_type)
        self.assertEqual('myseq', job_input_file.workflow_name)

        # Test dds_files
        url_files = job_input_file.url_files.all()
        self.assertEqual(1, len(url_files))
        url_file = url_files[0]
        self.assertEqual(job_input_file, url_file.job_input_file)
        self.assertEqual('https://data.org/sample.fasta', url_file.url)
        self.assertEqual('sample.fasta', url_file.destination_path)
        self.assertEqual(1, url_file.index)

    def test_url_file_array(self):
        job_input_file = JobInputFile.objects.create(job=self.job,
                                                     file_type=JobInputFile.DUKE_DS_FILE_ARRAY,
                                                     workflow_name='seq')
        URLJobInputFile.objects.create(job_input_file=job_input_file,
                                       url='https://data.org/sample.fasta',
                                       destination_path='sample.fasta',
                                       index=1)

        URLJobInputFile.objects.create(job_input_file=job_input_file,
                                       url='https://data.org/sample2.fasta',
                                       destination_path='sample2.fasta',
                                       index=2)

        job_input_file = JobInputFile.objects.first()
        self.assertEqual(self.job, job_input_file.job)
        self.assertEqual(JobInputFile.DUKE_DS_FILE_ARRAY, job_input_file.file_type)
        self.assertEqual('seq', job_input_file.workflow_name)
        url_files = job_input_file.url_files.all()
        self.assertEqual(2, len(url_files))
        self.assertIn('sample.fasta', [url_file.destination_path for url_file in url_files])
        self.assertIn('sample2.fasta', [url_file.destination_path for url_file in url_files])


class JobOutputDirTests(TestCase):
    def setUp(self):
        JobTests.add_job_fields(self)

    def test_basic_functionality(self):
        JobOutputDir.objects.create(job=self.job, dir_name='results', project_id='1234',
                                    dds_user_credentials=self.user_credentials)
        job_output_dir = JobOutputDir.objects.first()
        self.assertEqual(self.job, job_output_dir.job)
        self.assertEqual('results', job_output_dir.dir_name)
        self.assertEqual('1234', job_output_dir.project_id)
        self.assertEqual(self.user_credentials, job_output_dir.dds_user_credentials)


class LandoConnectionTests(TestCase):
    def test_basic_functionality(self):
        LandoConnection.objects.create(host='10.109.253.74', username='jpb67', password='secret', queue_name='lando')
        connection = LandoConnection.objects.first()
        self.assertEqual('10.109.253.74', connection.host)
        self.assertEqual('jpb67', connection.username)
        self.assertEqual('secret', connection.password)
        self.assertEqual('lando', connection.queue_name)


class JobErrorTests(TestCase):
    def setUp(self):
        JobTests.add_job_fields(self)

    def test_basic_functionality(self):
        JobError.objects.create(job=self.job,
                                content="Openstack ran out of floating IPs.",
                                job_step=Job.JOB_STEP_CREATE_VM)
        job_error = JobError.objects.first()
        self.assertEqual(self.job, job_error.job)
        self.assertEqual("Openstack ran out of floating IPs.", job_error.content)
        self.assertEqual(Job.JOB_STEP_CREATE_VM, job_error.job_step)
        self.assertIsNotNone(job_error.created)


class JobQuestionTests(TestCase):
    @staticmethod
    def create_rna_seq_job_questions():
        questions = []
        ques = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING)
        questions.append(ques)
        ques = JobQuestion.objects.create(key="gff_file", data_type=JobQuestionDataType.FILE)
        questions.append(ques)
        ques = JobQuestion.objects.create(key="reads", data_type=JobQuestionDataType.FILE, occurs=2)
        questions.append(ques)
        ques = JobQuestion.objects.create(key="ref_gene_model", data_type=JobQuestionDataType.FILE)
        questions.append(ques)
        ques = JobQuestion.objects.create(key="star_genome", data_type=JobQuestionDataType.FILE)
        questions.append(ques)
        ques = JobQuestion.objects.create(key="threads", data_type=JobQuestionDataType.INTEGER)
        questions.append(ques)
        return questions

    def test_write_list_job_questions(self):
        questions = JobQuestionTests.create_rna_seq_job_questions()
        self.assertEqual(6, len(questions))
        self.assertEqual(1, questions[0].occurs)
        self.assertEqual(1, questions[1].occurs)
        self.assertEqual(2, questions[2].occurs)
        self.assertEqual(1, questions[3].occurs)
        self.assertEqual(1, questions[4].occurs)
        self.assertEqual(1, questions[5].occurs)
        self.assertEqual(6, len(JobQuestion.objects.all()))


class JobQuestionnaireTests(TestCase):
    def setUp(self):
        self.workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=self.workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)

    def test_two_questionnaires(self):
        questions = JobQuestionTests.create_rna_seq_job_questions()
        self.assertEqual(6, len(questions))
        questionnaire = JobQuestionnaire.objects.create(name='Ant RnaSeq',
                                                        description='Uses reference genome xyz and gene index abc',
                                                        workflow_version=self.workflow_version)
        questionnaire.questions = questions
        questionnaire.save()

        questionnaire = JobQuestionnaire.objects.create(name='Human RnaSeq',
                                                        description='Uses reference genome zew and gene index def',
                                                        workflow_version=self.workflow_version)
        questionnaire.questions = questions
        questionnaire.save()

        ant_questionnaire = JobQuestionnaire.objects.filter(name='Ant RnaSeq').first()
        self.assertEqual('Ant RnaSeq', ant_questionnaire.name)
        self.assertEqual('Uses reference genome xyz and gene index abc', ant_questionnaire.description)
        self.assertEqual(6, len(ant_questionnaire.questions.all()))

        human_questionnaire = JobQuestionnaire.objects.filter(name='Human RnaSeq').first()
        self.assertEqual('Human RnaSeq', human_questionnaire.name)
        self.assertEqual('Uses reference genome zew and gene index def', human_questionnaire.description)
        self.assertEqual(6, len(human_questionnaire.questions.all()))


class JobAnswerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=self.workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)
        self.questions = JobQuestionTests.create_rna_seq_job_questions()
        self.question_map = {}
        for ques in self.questions:
            self.question_map[ques.key] = ques
        self.questionnaire = JobQuestionnaire.objects.create(description='Ant RnaSeq',
                                                             workflow_version=self.workflow_version)
        self.questionnaire.questions = self.questions
        self.questionnaire.save()

    def test_system_answers(self):
        """
        System answers will have questionnaire set.
        """
        gff_file = self.question_map['gff_file']
        gff_file_value = '/data/GCBA_RO/raw_data/genome_files/dmel-all-r5.53.gff'
        sys_job_answer = JobAnswer.objects.create(question=gff_file, questionnaire=self.questionnaire, user=self.user)
        self.assertEqual(0, sys_job_answer.index)
        JobStringAnswer.objects.create(answer=sys_job_answer, value=gff_file_value)

        ref_gene_model = self.question_map['ref_gene_model']
        ref_gene_model_value = '/data/GCBA_RO/raw_data/genome_files/dm3_flyBase.bed'
        sys_job_answer = JobAnswer.objects.create(question=ref_gene_model, questionnaire=self.questionnaire, user=self.user)
        self.assertEqual(0, sys_job_answer.index)
        JobStringAnswer.objects.create(answer=sys_job_answer, value=ref_gene_model_value)

        star_genome = self.question_map['star_genome']
        star_genome_value = '/data/GCBA_RO/generated_data/GenomeIndex'
        sys_job_answer = JobAnswer.objects.create(question=star_genome, questionnaire=self.questionnaire, user=self.user)
        self.assertEqual(0, sys_job_answer.index)
        JobStringAnswer.objects.create(answer=sys_job_answer, value=star_genome_value)

        threads = self.question_map['threads']
        threads_value = '8'
        sys_job_answer = JobAnswer.objects.create(question=threads, questionnaire=self.questionnaire, user=self.user)
        self.assertEqual(0, sys_job_answer.index)
        JobStringAnswer.objects.create(answer=sys_job_answer, value=threads_value)

        answers = JobAnswer.objects.filter(questionnaire=self.questionnaire)
        self.assertEqual(4, len(answers))
        gff_string_answer = JobStringAnswer.objects.filter(answer=answers[0]).first()
        self.assertEqual(gff_file_value, gff_string_answer.value)

    def test_user_answers(self):
        """
        User answers will NOT have questionnaire set and be part of a JobAnswerSet.
        """
        answer_set = JobAnswerSet.objects.create(questionnaire=self.questionnaire, user=self.user)
        answers = []
        align_out_prefix = self.question_map['align_out_prefix']
        align_out_prefix_value = 'bespin-rna-seq-0001_'
        self.assertEqual(1, align_out_prefix.occurs)
        user_job_answer = JobAnswer.objects.create(question=align_out_prefix, user=self.user)
        self.assertEqual(0, user_job_answer.index)
        JobStringAnswer.objects.create(answer=user_job_answer, value=align_out_prefix_value)
        answers.append(user_job_answer)

        endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        dds_user_credentials = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=endpoint)

        reads = self.question_map['reads']
        self.assertEqual(2, reads.occurs)
        user_job_answer = JobAnswer.objects.create(question=reads, index=1, user=self.user)
        JobDDSFileAnswer.objects.create(answer=user_job_answer,
                                        project_id='123',
                                        file_id='456',
                                        dds_user_credentials=dds_user_credentials)
        answers.append(user_job_answer)
        self.assertEqual('456', JobDDSFileAnswer.objects.filter(answer=user_job_answer).first().file_id)

        user_job_answer = JobAnswer.objects.create(question=reads, index=2, user=self.user)
        JobDDSFileAnswer.objects.create(answer=user_job_answer,
                                        project_id='123',
                                        file_id='457',
                                        dds_user_credentials=dds_user_credentials)
        answers.append(user_job_answer)

        answer_set.answers = answers
        answer_set.save()

        read_answer_set = JobAnswerSet.objects.filter(user=self.user).first()
        self.assertEqual(3, len(read_answer_set.answers.all()))

    def test_user_and_system_answers(self):
        """
        We should have a user or system answer for each question
        """
        self.test_system_answers()
        self.test_user_answers()
        answer_set = JobAnswerSet.objects.first()
        # There should be 3 user answers
        user_answers = list(answer_set.answers.all())
        self.assertEqual(3, len(user_answers))
        # There should be 4 system answers
        system_answers = list(JobAnswer.objects.filter(questionnaire=self.questionnaire).all())
        self.assertEqual(4, len(system_answers))

        # build a map of question keys to answer values
        answer_map = {}
        for answer in user_answers + system_answers:
            key = answer.question.key
            answer_list = answer_map.get(key, [])
            answer_list.append(answer)
            answer_map[key] = answer_list

        # make sure all questions now have an answer
        questions = answer_set.questionnaire.questions.all()
        self.assertEqual(6, len(questions))
        for question in questions:
            answer_list = answer_map.get(question.key, [])
            if question.key == 'reads':
                self.assertEqual(2, len(answer_list))
            else:
                self.assertEqual(1, len(answer_list))
