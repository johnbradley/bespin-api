from rest_framework.parsers import JSONParser


class JSONRootObjectParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        parsed = super(JSONRootObjectParser, self).parse(stream, media_type, parser_context)
        # Quick hack - we just assume if there's one key in the dictionary that the value is the payload
        # Should protect against this a little better. Maybe set parser to a different content-type?
        if len(parsed) == 1:
            return parsed.get(parsed.keys()[0])
        else:
            return parsed

