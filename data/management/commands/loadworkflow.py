from django.core.management.base import BaseCommand
from argparse import FileType
from data.models import Workflow, WorkflowVersion, JobQuestionnaire, VMFlavor, VMProject
from cwltool.load_tool import load_tool
from cwltool.workflow import defaultMakeTool
import json
import sys


class CWLDocument(object):
    """
    Simple CWL document parser
    """

    def __init__(self, url):
        """
        Creates a parser for the given URL
        :param url: The URL to a CWL document to be parsed
        """
        self.url = url
        self._parsed = None

    @property
    def parsed(self):
        """
        Lazy property to parse CWL on-demand
        :return: The CWL document, parsed into a dict
        """
        if self._parsed is None:
            self._parsed = load_tool(self.url + '#main', defaultMakeTool)
        return self._parsed

    @property
    def input_fields(self):
        """
        The input fields from the CWL document
        :return: List of input fields from the CWL document
        """
        return self.parsed.inputs_record_schema.get('fields')

    def get(self, key):
        """
        Gets the value of a key in the root of the CWL document
        :param key: The key to get
        :return: value associated with the key in the parsed CWL
        """
        return self.parsed.tool.get(key)


class BaseImporter(object):
    """
    Base for importer with simple logging facility
    """

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        """
        Creates a base importer with logging IO streams
        :param stdout: For writing info log messages
        :param stderr: For writing error messages
        """
        self.stdout = stdout
        self.stderr = stderr

    def log_creation(self, created, kind, name, id):
        if created:
            self.stdout.write("{} '{}' created with id {}".format(kind, name, id))
        else:
            self.stderr.write("{} '{}' already exists with id {}".format(kind, name, id))


class JobQuestionnaireImporter(BaseImporter):
    """
    Creates a JobQuestionnaire model for a WorkflowVersion with the supplied system job order
    """

    def __init__(self,
                 name,
                 description,
                 workflow_version,
                 system_job_order_file,
                 vm_flavor_name,
                 vm_project_name,
                 stdout=sys.stdout,
                 stderr=sys.stderr):
        super(JobQuestionnaireImporter, self).__init__(stdout, stderr)
        self.name = name
        self.description = description
        self.workflow_version = workflow_version
        self.system_job_order_dict = json.load(system_job_order_file)
        self.vm_flavor_name = vm_flavor_name
        self.vm_project_name = vm_project_name
        # django model objects built up
        self.vm_flavor = None
        self.vm_project = None
        self.job_questionnaire = None

    def _create_models(self):
        # vm flavor
        self.vm_flavor, created = VMFlavor.objects.get_or_create(vm_flavor=self.vm_flavor_name)
        self.log_creation(created, 'VMFlavor', self.vm_flavor_name, self.vm_flavor.id)
        # vm_project
        self.vm_project, created = VMProject.objects.get_or_create(vm_project_name=self.vm_project_name)
        self.log_creation(created, 'VMProject', self.vm_project_name, self.vm_project.id)

        # Extract fields that are not system-provided
        user_fields = []
        document = CWLDocument(self.workflow_version.url)
        for input_field in document.input_fields:
            if not input_field.get('name') in self.system_job_order_dict:
                user_fields.append(input_field)

        # Job questionnaire
        self.job_questionnaire, created = JobQuestionnaire.objects.get_or_create(
            name=self.name,
            description=self.description,
            workflow_version=self.workflow_version,
            system_job_order=json.dumps(self.system_job_order_dict),
            user_fields=json.dumps(user_fields),
            vm_flavor=self.vm_flavor,
            vm_project=self.vm_project,
        )
        self.log_creation(created, 'JobQuestionnaire', self.job_questionnaire.name, self.job_questionnaire.id)

    def run(self):
        self._create_models()

    def cleanup(self):
        self.job_questionnaire.delete()


class WorkflowImporter(BaseImporter):
    """
    Creates Workflow and WorkflowVersion model objects from a CWL document and supplied version number
    """

    def __init__(self,
                 cwl_url,
                 version_number=1,
                 stdout=sys.stdout,
                 stderr=sys.stderr):
        """
        Creates a WorkflowImporter to import the specified CWL and its variables into bespin-api models
        :param cwl_url: The URL to a CWL Workflow to import 
        :param version_number: the version number to assign
        :param stdout: For writing info log messages
        :param stderr: For writing error messages
        """
        super(WorkflowImporter, self).__init__(stdout, stderr)
        self.cwl_url = cwl_url
        self.version_number = version_number
        # django model objects built up
        self.workflow = None
        self.workflow_version = None

    def _create_models(self):
        document = CWLDocument(self.cwl_url)
        # Short description used for the Workflow name
        workflow_name = document.get('label')
        # Longer description used in workflow version
        workflow_version_description = document.get('doc')
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

    def cleanup(self):
        self.workflow_version.delete()
        self.workflow.delete()

    def run(self):
        # Parse in the workflow file
        self._create_models()


class Command(BaseCommand):
    help = 'Imports a workflow from CWL and creates a questionnaire. Will not alter existing model objects if they exist'

    def add_arguments(self, parser):
        parser.add_argument('cwl-url', help='URL to packed CWL workflow file. Do not include #main')
        parser.add_argument('version-number', help='Version number to assign to imported workflow')
        parser.add_argument('name', help='Short name to display forquestionnaire (e.g. ABC Processing on hg37)')
        parser.add_argument('description', help='Detailed user facing description of questionnaire')
        parser.add_argument('system-job-order-file', help='JSON Job order with system answers to associate with questionnaire '
                                                   '(e.g. reference genome files)', type=FileType('r'))
        parser.add_argument('vm-flavor', help='Name of VM flavor to use when running jobs(e.g. \'m1.large\')')
        parser.add_argument('vm-project', help='Name of Openstack to use when running jobs')

    def handle(self, *args, **options):
        wf_importer = WorkflowImporter(options.get('cwl-url'),
                                       version_number=options.get('version-number'),
                                       stdout=self.stdout,
                                       stderr=self.stderr)
        wf_importer.run()
        jq_importer = JobQuestionnaireImporter(
            options.get('name'),
            options.get('description'),
            wf_importer.workflow_version,
            options.get('system-job-order-file'),
            options.get('vm-flavor'),
            options.get('vm-project'),
            stdout=self.stdout,
            stderr=self.stderr,
        )
        jq_importer.run()
