from __future__ import absolute_import
from django.test import TestCase
from data.loaders import CWLDocument, MethodsDocumentContents, SCHEMA_ORG_CITATION, \
    HTTPS_DOI_URL
from mock import patch, Mock


class CWLNodeWithSteps(object):
    def __init__(self, steps):
        self.steps = steps


class CWLStepNode(object):
    def __init__(self, embedded_tool):
        self.embedded_tool = embedded_tool


class CWLNodeWithHints(object):
    def __init__(self, hints):
        self.hints = hints


class CWLDocumentTestCase(TestCase):
    def test_extract_tool_hints(self):
        cwl_document = CWLDocument('someurl')
        step_node1 = CWLStepNode(embedded_tool=CWLNodeWithHints(hints=[
            {
                'class': 'specialHint', 'value': 1
            }
        ]))
        step_node2 = CWLStepNode(embedded_tool=CWLNodeWithHints(hints=[
            {
                'class': 'specialHint', 'value': 2
            }
        ]))
        cwl_document._parsed = CWLNodeWithSteps(
            steps=[
                step_node1,
                CWLStepNode(
                    embedded_tool=CWLNodeWithSteps(
                        steps=[
                            step_node2
                        ]
                    )
                )
            ]
        )
        hints = cwl_document.extract_tool_hints('specialHint')
        self.assertEqual(set([1, 2]), set([hint['value'] for hint in hints]))


class MethodsDocumentContentsTestCase(TestCase):
    @patch('data.loaders.requests')
    @patch('data.loaders.cn')
    def test_get_content(self, mock_cn, mock_requests):

        software_requirement_hints = [
            {
                'packages': [
                    {
                        'package': 'sometool',
                        'version': '1',
                        SCHEMA_ORG_CITATION: 'someurl'
                    },
                    {
                        'package': 'othertool',
                        'version': '3',
                        SCHEMA_ORG_CITATION: HTTPS_DOI_URL + 'mydoi123'
                    },
                ]
            }
        ]
        jinja_template = """desc: {{description}} sometool version:{{sometool.version}} citation: {{sometool.citation}}
othertool version: {{othertool.version}} citation: {{othertool.citation}}"""
        expected_content = """desc: A good workflow sometool version:1 citation: someurl
othertool version: 3 citation: Dr Man 2017"""
        mock_requests.get.return_value = Mock(text=jinja_template)
        mock_cn.content_negotiation.return_value = 'Dr Man 2017'
        method_document_contents = MethodsDocumentContents(
            workflow_version_description='A good workflow',
            software_requirement_hints=software_requirement_hints,
            jinja_template_url='fakeurl')
        self.assertEqual(expected_content, method_document_contents.get_content())


class QuestionnaireLoaderTestCase(TestCase):

    def test_loader(self):
        self.fail('Not yet implemented')
