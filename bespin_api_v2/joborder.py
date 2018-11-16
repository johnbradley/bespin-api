from data.jobfactory import JobFactory
from data.models import WorkflowVersion, WorkflowConfiguration

STRING_VALUE_PLACEHOLDER = "<String Value>"
INT_VALUE_PLACEHOLDER = "<Integer Value>"
FILE_PLACEHOLDER = "dds://<Project Name>/<File Path>"
USER_PLACEHOLDER_VALUES = [STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER]
USER_PLACEHOLDER_DICT = {
    'File': {
        "class": "File",
        "path": FILE_PLACEHOLDER
    },
    'int': INT_VALUE_PLACEHOLDER,
    'string': STRING_VALUE_PLACEHOLDER,
    'NamedFASTQFilePairType': {
        "name": STRING_VALUE_PLACEHOLDER,
        "file1": {
            "class": "File",
            "path": FILE_PLACEHOLDER
        },
        "file2": {
            "class": "File",
            "path": FILE_PLACEHOLDER
        }
    },
    'FASTQReadPairType': {
        "name": STRING_VALUE_PLACEHOLDER,
        "read1_files": [{
            "class": "File",
            "path": FILE_PLACEHOLDER
        }],
        "read2_files": [{
            "class": "File",
            "path": FILE_PLACEHOLDER
        }]
    }
}


class WorkflowVersionConfiguration(object):
    def __init__(self, tag):
        workflow_tag, version_num, configuration_name = self.split_workflow_tag_parts(tag)
        self.workflow_version = WorkflowVersion.objects.get(
            version=version_num,
            workflow__tag=workflow_tag)
        self.workflow_configuration = WorkflowConfiguration.objects.get(
            workflow=self.workflow_version.workflow,
            name=configuration_name)

    @staticmethod
    def split_workflow_tag_parts(tag):
        """
        Based on our tag return tuple of base_workflow_tag, version_num, configuration_name
        :param tag: str: tag to split into parts
        :return: (workflow_tag, version_num, configuration_name)
        """
        parts = tag.split("/")
        if len(parts) != 3:
            return None
        workflow_tag, version_num_str, configuration_name = parts
        version_num = int(version_num_str.replace("v", ""))
        return workflow_tag, version_num, configuration_name

    def user_job_fields(self):
        system_keys = self.workflow_configuration.system_job_order.keys()
        user_fields_json = []
        for field in self.workflow_version.fields:
            if field['name'] not in system_keys:
                user_fields_json.append(field)
        return user_fields_json


class JobFile(object):
    def __init__(self, workflow_tag, name=STRING_VALUE_PLACEHOLDER, fund_code=STRING_VALUE_PLACEHOLDER, job_order=None):
        self.workflow_tag = workflow_tag
        self.name = name
        self.fund_code = fund_code
        if job_order:
            self.job_order = job_order
        else:
            self.job_order = self._create_job_order()

    def _create_job_order(self):
        workflow_version_config = WorkflowVersionConfiguration(self.workflow_tag)
        formatted_user_fields = {}
        for user_field in workflow_version_config.user_job_fields():
            field_type = user_field.get('type')
            field_name = user_field.get('name')
            if isinstance(field_type, dict):
                if field_type['type'] == 'array':
                    value = self.create_placeholder_value(field_type['items'], is_array=True)
                else:
                    value = self.create_placeholder_value(field_type['type'], is_array=False)
            else:
                value = self.create_placeholder_value(field_type, is_array=False)
            formatted_user_fields[field_name] = value
        return formatted_user_fields

    def create_placeholder_value(self, type_name, is_array):
        if is_array:
            return [self.create_placeholder_value(type_name, is_array=False)]
        else:  # single item type
            placeholder = USER_PLACEHOLDER_DICT.get(type_name)
            if not placeholder:
                return STRING_VALUE_PLACEHOLDER
            return placeholder


class JobOrderData(object):
    def __init__(self, workflow_tag, name, fund_code, stage_group, job_order, share_group, job_vm_strategy=None):
        self.workflow_tag = workflow_tag
        self.name = name
        self.fund_code = fund_code
        self.stage_group = stage_group
        self.job_order = job_order
        self.share_group = share_group
        self.job_vm_strategy = job_vm_strategy

    def get_vm_strategy(self, workflow_configuration):
        if self.job_vm_strategy:
            return self.job_vm_strategy
        else:
            return workflow_configuration.default_vm_strategy

    def create_job_factory(self, user):
        workflow_version_configuration = WorkflowVersionConfiguration(self.workflow_tag)
        system_job_order = workflow_version_configuration.workflow_configuration.system_job_order
        vm_strategy = self.get_vm_strategy(workflow_version_configuration.workflow_configuration)
        return JobFactory(user, workflow_version_configuration.workflow_version,
                          self.name, self.fund_code, self.stage_group,
                          system_job_order, self.job_order,
                          vm_strategy, self.share_group)

    def create_job(self, user):
        job_factory = self.create_job_factory(user)
        return job_factory.create_job()
