from data.jobfactory import WorkflowVersionConfiguration

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
