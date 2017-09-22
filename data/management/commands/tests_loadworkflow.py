from __future__ import absolute_import
from django.test import TestCase
from data.management.commands.loadworkflow import CWLDocument
from mock import Mock



class NodeWithSteps(object):
    def __init__(self, steps):
        self.steps = steps

class StepNode(object):
    def __init__(self, embedded_tool):
        self.embedded_tool = embedded_tool

class NodeWithHints(object):
    def __init__(self, hints):
        self.hints = hints


class CWLDocumentTestCase(TestCase):
    def test_extract_tool_hints(self):
        cwl_document = CWLDocument('someurl')
        step_node1 = StepNode(embedded_tool=NodeWithHints(hints=[
            {
                'class': 'specialHint', 'value': 1
            }
        ]))
        step_node2 = StepNode(embedded_tool=NodeWithHints(hints=[
            {
                'class': 'specialHint', 'value': 2
            }
        ]))
        cwl_document._parsed = NodeWithSteps(
            steps=[
                step_node1,
                StepNode(
                    embedded_tool=NodeWithSteps(
                        steps=[
                            step_node2
                        ]
                    )
                )
            ]
        )
        hints = cwl_document.extract_tool_hints('specialHint')
        self.assertEqual(set([1, 2]), set([hint['value'] for hint in hints]))
