from data.models import JobAnswer, JobAnswerKind, JobDDSFileAnswer, JobStringAnswer, JobQuestionDataType, \
    Job, JobOutputDir
from rest_framework.exceptions import ValidationError
from util import get_file_name
from exceptions import QuestionnaireExceptions

# Special fields
# job.name
# job.vm_project_name
# job.output_directory directory name and project id
# job.vm_flavor

JOB_FIELD_PREFIX = "job."
JOB_FIELD_NAME = "{}name".format(JOB_FIELD_PREFIX)
JOB_FIELD_PROJECT_NAME = "{}vm_project_name".format(JOB_FIELD_PREFIX)
JOB_FIELD_VM_FLAVOR = "{}vm_flavor".format(JOB_FIELD_PREFIX)
JOB_FIELD_OUTPUT_DIRECTORY = "{}output_directory".format(JOB_FIELD_PREFIX)

def create_job_factory(user, job_answer_set):
    factory = JobFactory(user, job_answer_set.questionnaire.workflow_version)
    for question in job_answer_set.questionnaire.questions.all():
        factory.add_question(question)
    for user_answer in job_answer_set.answers.all():
        factory.add_answer(user_answer)
    for system_answer in JobAnswer.objects.filter(questionnaire=job_answer_set.questionnaire.id):
        factory.add_answer(system_answer)
    return factory


class JobFactory(object):
    def __init__(self, user, workflow_version):
        self.workflow_version = workflow_version
        self.user = user
        self.questions = []
        self.answers = []

    def add_question(self, question):
        self.questions.append(question)

    def add_answer(self, answer):
        self.answers.append(answer)

    def create_job(self):
        job_name = None
        vm_project_name = None
        vm_flavor = None
        output_directory = None
        question_key_map = QuestionKeyMap()
        question_key_map.add_questions(self.questions)
        question_key_map.add_answers(self.answers)
        errors = question_key_map.get_errors()
        if errors:
            raise QuestionnaireExceptions(errors)
        cwl_input = {}
        for key, question_info in question_key_map.map.items():
            if key.startswith(JOB_FIELD_PREFIX):
                value = self.format_answers(question_info)
                if key == JOB_FIELD_NAME:
                    job_name = value
                elif key == JOB_FIELD_PROJECT_NAME:
                    vm_project_name = value
                elif key == JOB_FIELD_VM_FLAVOR:
                    vm_flavor = value
                elif key == JOB_FIELD_OUTPUT_DIRECTORY:
                    output_directory = value
                else:
                    raise ValidationError("Invalid job field question name {}".format(key))
            else:
                cwl_input[key] = self.format_answers(question_info)

        job = Job.objects.create(workflow_version=self.workflow_version,
                                  user=self.user,
                                  name=job_name,
                                  vm_project_name=vm_project_name,
                                  vm_flavor=vm_flavor,
                                  workflow_input_json=cwl_input)
        JobOutputDir.objects.create(job=job,
                                    dir_name=output_directory.directory_name,
                                    project_id=output_directory.project_id,
                                    dds_user_credentials=output_directory.dds_user_credentials)
        return job

    def _build_cwl_input(self):
        question_key_map = QuestionKeyMap()
        question_key_map.add_questions(self.questions)
        question_key_map.add_answers(self.answers)
        errors = question_key_map.get_errors()
        if errors:
            raise QuestionnaireExceptions(errors)
        result = {}
        for key, question_info in question_key_map.map.items():
            if not key.startswith(JOB_FIELD_PREFIX):
                result[key] = self.format_answers(question_info)
        return result

    def format_answers(self, question_info):
        question = question_info.question
        if question_info.question.occurs == 1:
            return self.format_single_answer(question, question_info.answers[0])
        else:
            array_answer = []
            for answer in sorted(question_info.answers, key=lambda answer: answer.index):
                array_answer.append(self.format_single_answer(question, answer))
            return array_answer

    def format_single_answer(self, question, answer):
        data_type = question.data_type
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
        dds_file = answer.dds_file
        filename = get_file_name(self.user, dds_file.file_id)
        return '{}_{}'.format(answer.id, filename)


class QuestionKeyMap(object):
    def __init__(self):
        self.map = {}

    def add_questions(self, questions):
        for question in questions:
            key = question.key
            question_info = self.map.get(key, None)
            if question_info:
                question_info.duplicate = True
            else:
                self.map[key] = QuestionInfo(question)

    def add_answers(self, answers):
        for answer in answers:
            key = answer.question.key
            question_info = self.map.get(key, None)
            if question_info:  # A question exists for this answer
                question_info.add_answer(answer)
            else:  # We have an answer with no question
                question_info = QuestionInfo(answer.question)
                question_info.answer_without_question = True
                question_info.add_answer(answer)
                self.map[key] = question_info

    def get_errors(self):
        errors = []
        for key, question_info in self.map.items():
            for error in question_info.get_errors():
                errors.append({
                    "source": question_info.question.key,
                    "details": error,
                })
        return errors


class QuestionInfo(object):
    def __init__(self, question):
        self.duplicate = False
        self.answer_without_question = False
        self.question = question
        self.answers = []

    def add_answer(self, answer):
        self.answers.append(answer)

    def get_errors(self):
        errors = []
        if self.duplicate:
            errors.append("Setup error: Multiple questions with same key: {}.".format(self.question.key))
        if self.answer_without_question:
            errors.append("Setup error: Answer without question: {}.".format(self.question.key))
        if len(self.answers) == 0:
            errors.append("Required field.".format(self.question.key))
        return errors
