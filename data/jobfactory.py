from data.models import Job, JobOutputDir, JobInputFile, DDSJobInputFile
from rest_framework.exceptions import ValidationError
from util import get_file_name
from exceptions import JobFactoryException
import json

# Fields that are added to CWL input(Job.job_order) must begin with this prefix
JOB_ORDER_PREFIX = "job_order."
# Fields that update properties of the Job tables
JOB_QUESTION_NAME = "name"
JOB_QUESTION_PROJECT_NAME = "vm_project_name"
JOB_QUESTION_VM_FLAVOR = "vm_flavor"
JOB_QUESTION_OUTPUT_DIRECTORY = "output_directory"
JOB_QUESTIONS = [
    JOB_QUESTION_NAME,
    JOB_QUESTION_PROJECT_NAME,
    JOB_QUESTION_VM_FLAVOR,
    JOB_QUESTION_OUTPUT_DIRECTORY,
]


def create_job_factory(user, job_answer_set):
    """
    Create JobFactory based on questions and answers referenced by job_answer_set.
    :param user: User: user who's credentials we will use for building the job
    :param job_answer_set: JobAnswerSet: references questions and their answers to use for building a Job.
    :return: JobFactory
    """
    factory = JobFactory(user, job_answer_set.questionnaire.workflow_version)
    raise NotImplementedError
    return factory


class JobFactory(object):
    """
    Creates Job record in the database based on questions their answers.
    """
    def __init__(self, user, workflow_version):
        """
        Setup factory
        :param user: User: user we are creating this job for and who's credentials we will use
        :param workflow_version: WorkflowVersion: which CWL workflow are we building a job for
        """
        self.workflow_version = workflow_version
        self.user = user
        self.questions = []
        self.answers = []

    def add_question(self, question):
        """
        Add a question to the list of questions that will be used to build the job.
        :param question: JobQuestion: question that will fill in some part of the Job
        """
        self.questions.append(question)

    def add_answer(self, answer):
        """
        Add an answer to a question that was or will be added via add_question.
        :param answer: JobAnswer
        """
        self.answers.append(answer)

    def create_job(self):
        """
        Create a job based on the workflow_version, questions and answers.
        Raises ValidationError if there is a problem with the answers.
        :return: Job: job that was inserted into the database along with it's output directory and input files.
        """
        self._check_for_missing_job_questions()
        question_info_list = self._build_question_info_list()
        job_fields = JobFields(question_info_list)
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 user=self.user,
                                 name=job_fields.job_name,
                                 vm_project_name=job_fields.vm_project_name,
                                 vm_flavor=job_fields.vm_flavor,
                                 job_order=job_fields.job_order)
        output_directory = job_fields.output_directory
        JobOutputDir.objects.create(job=job,
                                    dir_name=output_directory.directory_name,
                                    project_id=output_directory.project_id,
                                    dds_user_credentials=output_directory.dds_user_credentials)
        self._insert_job_input_files(job, question_info_list)
        return job

    def _check_for_missing_job_questions(self):
        """
        Make sure we have questions for all the required job fields.
        If not raise an exception so an admin can fix the setup.
        """
        question_names = set(JOB_QUESTIONS)
        for question in self.questions:
            key = question.key
            if key in question_names:
                question_names.remove(key)
        if question_names:
            raise ValidationError("Setup error: Missing questions {}".format(','.join(question_names)))

    def _build_question_info_list(self):
        """
        Build a question list based on the internal questions and answers.
        Raises JobFactoryException if there were any errors
        :return: QuestionInfoList: a list of Questions/Answers
        """
        question_info_list = QuestionInfoList(self.user)
        question_info_list.add_questions(self.questions)
        question_info_list.add_answers(self.answers)
        errors = question_info_list.get_errors()
        if errors:
            raise JobFactoryException(errors)
        return question_info_list

    def _insert_job_input_files(self, job, question_info_list):
        """
        Insert JobInputFile records for each input file answer in the question_info_list under the specified job.
        :param job: Job: job that we will add JobInputFiles under
        :param question_info_list: QuestionInfoList: contains answers we will
        """
        for question_info in question_info_list.values():
            job_answers = question_info.get_answers_by_kind(JobAnswerKind.DDS_FILE)
            if job_answers:
                type = JobInputFile.DUKE_DS_FILE
                if question_info.question.occurs > 2:
                    type = JobInputFile.DUKE_DS_FILE_ARRAY
                job_input_file = JobInputFile.objects.create(job=job,
                                                             file_type=type,
                                                             workflow_name=question_info.key)
                for job_answer in job_answers:
                    job_dds_file_answer = job_answer.dds_file
                    DDSJobInputFile.objects.create(
                        job_input_file=job_input_file,
                        project_id=job_dds_file_answer.project_id,
                        file_id=job_dds_file_answer.file_id,
                        dds_user_credentials=job_dds_file_answer.dds_user_credentials,
                        destination_path=question_info.get_unique_dds_filename(job_answer),
                        index=job_answer.index
                    )


class QuestionInfoList(object):
    """
    List of QuestionInfo objects built by adding questions and their answers.
    """
    def __init__(self, user):
        """
        Setup QuestionInfoList
        :param user: User: user that has credentials for looking up DDS data
        """
        self.key_to_item = {}
        self.user = user

    def add_questions(self, questions):
        """
        Add a list of questions.
        :param questions: [JobQuestion]: questions to add to our list
        """
        for question in questions:
            key = question.key
            question_info = self.key_to_item.get(key, None)
            if question_info:
                question_info.duplicate = True
            else:
                self.key_to_item[key] = QuestionInfo(question, self.user)

    def add_answers(self, answers):
        """
        Add a list of answers to questions that have already been added.
        :param answers: [JobAnswer]: answers to previously added questions
        """
        for answer in answers:
            key = answer.question.key
            question_info = self.key_to_item.get(key, None)
            if question_info:  # A question exists for this answer
                question_info.add_answer(answer)
            else:  # We have an answer with no question
                question_info = QuestionInfo(answer.question, self.user)
                question_info.answer_without_question = True
                question_info.add_answer(answer)
                self.key_to_item[key] = question_info

    def values(self):
        """
        Return a list of all QuestionInfo objects
        :return: [QuestionInfo]: list of questions and their answers
        """
        return self.key_to_item.values()

    def get_errors(self):
        """
        Return a list of errors based on the questions and answers added to the list.
        :return: [dict]: list of dictionaries with "source" and "details" values.
        """
        errors = []
        for question_info in self.values():
            for error in question_info.get_errors():
                errors.append({
                    "source": question_info.question.key,
                    "details": error,
                })
        return errors


class QuestionInfo(object):
    """
    Contains question and answers for that question as well as error flags.
    """
    def __init__(self, question, user):
        """
        Create info object for a question.
        :param question: JobQuestion: question we will add answers for
        """
        self.question = question
        self.key = question.key
        self.duplicate = False
        self.answer_without_question = False
        self.answers = []
        self.user = user

    def add_answer(self, answer):
        """
        Add answer to the list of answers for the question passed in the constructor.
        :param answer: JobAnswer: answer that was for our question
        """
        self.answers.append(answer)

    def get_errors(self):
        """
        Return a list of errors based on this question and it's answers
        :return: [str]: array of error messages
        """
        errors = []
        if self.duplicate:
            errors.append("Setup error: Multiple questions with same key: {}.".format(self.question.key))
        if self.answer_without_question:
            errors.append("Setup error: Answer without question: {}.".format(self.question.key))
        if len(self.answers) == 0:
            errors.append("Required field.".format(self.question.key))
        return errors

    def get_answers_by_kind(self, answer_kind):
        """
        Lookup answers based on their type.
        :param answer_kind: str: JobAnswerKind value for which answers to include
        :return: [JobAnswer] any answers for this question that are of answer_kind type
        """
        result = []
        for answer in self.answers:
            if answer.kind == answer_kind:
                result.append(answer)
        return result

    def get_formatted_answers(self):
        """
        Format the answer or answers based on the question data_type and the answer kind.
        :return: array of objects or single object
        """
        if self.question.occurs == 1:
            return self.format_single_answer(self.answers[0])
        else:
            array_answer = []
            for answer in sorted(self.answers, key=lambda answer: answer.index):
                array_answer.append(self.format_single_answer(answer))
            return array_answer

    def format_single_answer(self, answer):
        """
        Format a single answer based on the data type of our question and the answer kind.
        :param answer: JobAnswer: answer to format
        :return: object: format varies based on question data type
        """
        data_type = self.question.data_type
        answer_kind = answer.kind
        if answer_kind == JobAnswerKind.STRING:
            value = answer.string_value.value
            if data_type == JobQuestionDataType.STRING:
                return value
            if data_type == JobQuestionDataType.INTEGER:
                return int(value)
            if data_type == JobQuestionDataType.FILE:
                return {
                    "class": "File",
                    "path": value
                }
            if data_type == JobQuestionDataType.DIRECTORY:
                return {
                    "class": "Directory",
                    "path": value
                }
        if answer_kind == JobAnswerKind.DDS_FILE:
            filename = self.get_unique_dds_filename(answer)
            if data_type == JobQuestionDataType.FILE:
                return {
                    "class": "File",
                    "path": filename
                }
        if answer_kind == JobAnswerKind.DDS_OUTPUT_DIRECTORY:
            dds_output_directory = answer.dds_output_directory
            if data_type == JobQuestionDataType.DIRECTORY:
                return dds_output_directory
        raise ValidationError("Unsupported question data type: {} and answer kind: {}".format(data_type, answer_kind))

    def get_unique_dds_filename(self, answer):
        """
        Lookup the name of the a DukeDS file and add a unique prefix to it.
        :param answer: JobAnswer: answer we want to create a unique filename for
        :return: str: unique filename created by prefixing the name from DukeDS
        """
        dds_file = answer.dds_file
        filename = get_file_name(self.user, dds_file.file_id)
        return '{}_{}'.format(answer.id, filename)


class JobFields(object):
    """
    Pulls out job fields from a question_info_list
    """
    def __init__(self, question_info_list):
        """
        Pull out Job fields from question_info_list.
        Raises ValidationError for bogus names.
        :param question_info_list: QuestionInfoList: contains questions and their answers that become job fields
        """
        self.job_name = None
        self.vm_project_name = None
        self.vm_flavor = None
        self.output_directory = None
        job_order = {}
        for question_info in question_info_list.values():
            key = question_info.key
            if key.startswith(JOB_ORDER_PREFIX):
                job_order_key = key.replace(JOB_ORDER_PREFIX, "", 1)
                job_order[job_order_key] = question_info.get_formatted_answers()
            else:
                value = question_info.get_formatted_answers()
                if key == JOB_QUESTION_NAME:
                    self.job_name = value
                elif key == JOB_QUESTION_PROJECT_NAME:
                    self.vm_project_name = value
                elif key == JOB_QUESTION_VM_FLAVOR:
                    self.vm_flavor = value
                elif key == JOB_QUESTION_OUTPUT_DIRECTORY:
                    self.output_directory = value
                else:
                    raise ValidationError("Invalid job field question name {}".format(key))
        self.job_order = json.dumps(job_order)
