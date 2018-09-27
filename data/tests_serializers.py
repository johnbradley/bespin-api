from django.test import TestCase
from data.serializers import AdminImportWorkflowQuestionnaireSerializer

class AdminImportWorkflowQuestionnaireSerializerTest(TestCase):

    def setUp(self):
        self.valid_data = {
            "cwl_url": "https://github.com/Duke-GCB/bespin-cwl/releases/download/v0.9.0/exomeseq.cwl",
            "workflow_version_number": 4,
            "name": "Whole Exome Sequence analysis using GATK best practices - Germline SNP & Indel Discovery",
            "description" : "This is a whole-exome sequencing using the b37 human genome assembly, GATK, and a SeqCap EZ Exome v3 capture kit.",
            "methods_template_url": "https://raw.githubusercontent.com/Duke-GCB/bespin-cwl/v0.9.0/workflows/exomeseq-methods.j2",
            "system_json": {    # JSON to store for this workflow
            },
            "vm_settings_name": "name of vm settings",
            "vm_flavor_name": "m1.xlarge",
            "share_group_name": "Informatics",
            "volume_size_base": 1000,
            "volume_size_factor": 10,
            "workflow_tag": "my-tag",
            "type_tag": "human",
        }

    def test_valid(self):
        serializer = AdminImportWorkflowQuestionnaireSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_required_fields(self):
        serializer = AdminImportWorkflowQuestionnaireSerializer(data={})
        self.assertFalse(serializer.is_valid())

        self.assertIn('cwl_url', serializer.errors)
        self.assertIn('workflow_version_number', serializer.errors)
        error_fields_set = set(serializer.errors.keys())
        self.assertSetEqual(error_fields_set, {'cwl_url',
                                               'workflow_version_number',
                                               'name',
                                               'description',
                                               'workflow_tag',
                                               'type_tag',
                                               'methods_template_url',
                                               'system_json',
                                               'vm_settings_name',
                                               'vm_flavor_name',
                                               'share_group_name',
                                               'volume_size_base',
                                               'volume_size_factor',})
