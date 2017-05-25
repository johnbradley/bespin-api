from django.core.management.base import BaseCommand
from argparse import FileType
from data.models import Workflow, WorkflowVersion, JobQuestion, JobQuestionDataType
from cwltool.load_tool import load_tool
from cwltool.workflow import defaultMakeTool
import json
import sys

class FieldProcessor(object):
    # Must be overridden
    data_type = None

    def __init__(self, key, name, importer, occurs=1):
        self.key = key
        self.name = name
        self.importer = importer
        self.question = None
        self.occurs = occurs

    def process(self):
        question, created = JobQuestion.objects.get_or_create(
            key=self.key,
            name=self.name,
            data_type=self.data_type,
            occurs=self.occurs
        )
        self.importer.log_creation(created, 'Question', question.key, question.id)
        self.question = question

        if self.importer.is_system_field(self.key):
            self.process_system()
        else:
            self.process_user()

    def process_system(self):
        pass

    def process_user(self):
        pass


class StringFieldProcessor(FieldProcessor):
    data_type = JobQuestionDataType.STRING


class FileFieldProcessor(FieldProcessor):
    data_type = JobQuestionDataType.FILE


class DoubleFieldProcessor(FieldProcessor):
    data_type = JobQuestionDataType.DOUBLE


class IntFieldProcessor(FieldProcessor):
    data_type = JobQuestionDataType.INTEGER


class WorkflowImporter(object):

    def __init__(self, cwl_url, system_answers_job_order_file, version_number=1, stdout=sys.stdout, stderr=sys.stderr):
        """
        Creates a WorkflowImporter to import the specified CWL and its variables into bespin-api models
        :param cwl_url: The URL to a CWL Workflow to import 
        :param system_answers_job_order_file: a CWL job order file that will supply the system-provided answers 
        (e.g. reference genomes or other system-defined variables)
        :param version_number: the version number to assign
        :param stdout: For writing info log messages
        :param stderr: For writing error messages
        """
        self.cwl_url = cwl_url
        self.system_answers_job_order = json.load(system_answers_job_order_file)
        self.version_number = version_number
        self.parsed_cwl = load_tool(self.cwl_url, defaultMakeTool)
        self.stdout = stdout
        self.stderr = stderr
        # django model objects built up
        self.workflow = None
        self.workflow_version = None

    def _get_cwl_input_fields(self):
        return self.parsed_cwl.inputs_record_schema.get('fields')

    def log_creation(self, created, kind, name, id):
        if created:
            self.stdout.write("{} '{}' created with id {}".format(kind, name, id))
        else:
            self.stderr.write("{} '{}' already exists with id {}".format(kind, name, id))

    def _create_workflow_models(self):
        # Short description used for the Workflow name
        workflow_name = self.parsed_cwl.tool.get('label')
        # Longer description used in workflow version
        workflow_version_description = self.parsed_cwl.tool.get('doc')
        workflow, created = Workflow.objects.get_or_create(name=workflow_name)
        self.log_creation(created, 'Workflow', workflow_name, workflow.id)
        workflow_version, created = WorkflowVersion.objects.get_or_create(
            workflow=workflow,
            url=self.cwl_url,
            description=workflow_version_description,
            version=self.version_number,
        )
        self.log_creation(created, 'Workflow Version', workflow_version_description, workflow_version.id)
        self.workflow = workflow
        self.workflow_version = workflow_version

    def _create_job_question_object(self, stuff):
        pass

    def is_system_field(self, field_name):
        return field_name in self.system_answers_job_order

    @staticmethod
    def unwrap_optional_type(field_type):
        # optionals are represented by [u'null', ordereddict([('type', 'array'), ('items', 'string')])]
        if isinstance(field_type, list) and field_type[0] == 'null':
            # for optionals, return the non-null type
            return True, field_type[-1]
        else:
            return False, field_type

    @staticmethod
    def unwrap_array_type(field_type):
        print 'trying to unwrap array'
        try:
            # Array types in CWL are ruamel CommentedMap.
            # We'll try it and fall back if not
            field_type, item_type = (field_type.get(x) for x in ('type', 'items'))
            if field_type == 'array':
                print 'unwrapping item type', item_type
                return True, item_type
        except:
            pass
        return False, field_type

    processor_classes = {
        'File': FileFieldProcessor,
        'string': StringFieldProcessor,
        'double': DoubleFieldProcessor,
        'int': IntFieldProcessor,
    }

    def _process_fields(self):
        fields = self._get_cwl_input_fields()
        # For each field we need to create a question
        # If the field is listed in
        for field in fields:
            occurs = 1
            field_type, key = (field.get(x) for x in ('type','name'))
            optional, field_type = self.unwrap_optional_type(field_type)
            array = True
            while array is True:
                array, field_type = self.unwrap_array_type(field_type)
            if array:
                print 'Array!'
                occurs = 2 # TODO: Get actual number
            self.stdout.write('processing field {} of type {}'.format(key, field_type))
            processor_class = self.processor_classes.get(field_type)
            processor = processor_class(key, 'NAME GOES HERE', self, occurs)
            processor.process()

    def cleanup(self):
        self.workflow_version.delete()
        self.workflow.delete()

    def run(self):
        # Parse in the workflow file
        self._create_workflow_models()
        # Create JobQuestions
        # Create a questionnaire, linking questions to a workflowversion
        # Create JobAnswer for system answers. How to denote this in the workflow? sys prefix? other metadata attributes in workflow? Maybe a label or doc convention
        self._process_fields()

class Command(BaseCommand):
    help = 'Imports a workflow from CWL'

    def add_arguments(self, parser):
        parser.add_argument('cwl-url', help='URL to CWL workflow file. If packed, terminate with #main')
        parser.add_argument('job-order-file', help='JSON Job order with system answers to associate with questionnaire '
                                                   '(e.g. reference genome files)', type=FileType('r'))
        parser.add_argument('version-number', help='Version number to assign to imported workflow')

    def handle(self, *args, **options):
        version_number = options.get('version-number')
        importer = WorkflowImporter(options.get('cwl-url'),
                                    options.get('job-order-file'),
                                    version_number=version_number,
                                    stdout=self.stdout,
                                    stderr=self.stderr)
        importer.run()
        # importer.cleanup()
