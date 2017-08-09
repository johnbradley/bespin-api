import sys

class CommandLogger(object):
    """
    Base for command with simple logging facility
    """

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        """
        Creates a base command logger  with logging IO streams
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

    def log(self, message):
        self.stdout.write(message)

