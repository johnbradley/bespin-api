from django.test import TestCase
from parsers import JSONRootObjectParser, ParseError

from mock import MagicMock
import StringIO
import json

class JSONRootObjectParserTestCase(TestCase):

    def setUp(self):
        self.parser = JSONRootObjectParser()
        self.object = {'objects':{'size':'medium'}}
        self.json = json.dumps(self.object)
        # Configure mock parser_context
        mock_view = MagicMock()
        serializer = MagicMock()
        self.mock_serializer = serializer
        serializer.Meta = MagicMock(resource_name='objects')
        mock_view.get_serializer = MagicMock(return_value=serializer)
        self.parser_context = {'view': mock_view}

    def _parse(self):
        return self.parser.parse(StringIO.StringIO(self.json), JSONRootObjectParser.media_type, self.parser_context)

    def test_parses_resource(self):
        self.assertTrue(hasattr(self.mock_serializer.Meta, 'resource_name'))
        parsed = self._parse()
        self.assertEqual(parsed, self.object['objects'])

    def test_raises_parse_error_when_no_resource_name(self):
        delattr(self.mock_serializer.Meta, 'resource_name')
        self.assertFalse(hasattr(self.mock_serializer.Meta, 'resource_name'))
        with self.assertRaises(ParseError):
            self._parse()

    def test_raises_key_error(self):
        self.mock_serializer.Meta = MagicMock(resource_name='others')
        self.assertTrue(hasattr(self.mock_serializer.Meta, 'resource_name'))
        with self.assertRaises(ParseError):
            self._parse()

