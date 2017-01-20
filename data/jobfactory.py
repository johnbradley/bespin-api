from data.models import JobAnswer, JobAnswerKind, JobDDSFileAnswer, JobStringAnswer, JobQuestionDataType
from rest_framework.exceptions import ValidationError
from util import get_file_name
from exceptions import QuestionnaireExceptions


def create_job_factory(user, job_answer_set):
    factory = JobFactory(user)
    for question in job_answer_set.questionnaire.questions.all():
        factory.add_question(question)
    for user_answer in job_answer_set.answers.all():
        factory.add_answer(user_answer)
    for system_answer in JobAnswer.objects.filter(questionnaire=job_answer_set.questionnaire.id):
        factory.add_answer(system_answer)
    return factory


class JobFactory(object):
    def __init__(self, user):
        self.user = user
        self.questions = []
        self.answers = []

    def add_question(self, question):
        self.questions.append(question)

    def add_answer(self, answer):
        self.answers.append(answer)

    def build_cwl_input(self):
        question_key_map = QuestionKeyMap()
        question_key_map.add_questions(self.questions)
        question_key_map.add_answers(self.answers)
        errors = question_key_map.get_errors()
        if errors:
            raise QuestionnaireExceptions(errors)
        result = {}
        for key, question_info in question_key_map.map.items():
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
