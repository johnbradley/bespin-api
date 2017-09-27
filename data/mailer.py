from django.core.mail import EmailMessage as DjangoEmailMessage
from django.template import Template, Context
from django.utils.safestring import mark_safe
from models import EmailMessage, EmailTemplate


class EmailMessageFactory(object):

    def __init__(self, email_template):
        self.email_template = email_template

    @classmethod
    def _render(cls, template, context):
        for k in context:
            context[k] = mark_safe(context[k])
        django_template = Template(template)
        return django_template.render(Context(context))

    def _render_subject(self, context):
        return self._render(self.email_template.subject_template, context)

    def _render_body(self, context):
        return self._render(self.email_template.body_template, context)

    def make_message(self, context, sender_email, to_email):
        body = self._render_body(context)
        subject = self._render_subject(context)
        message = EmailMessage.objects.create(
            body=body,
            subject=subject,
            sender_email=sender_email,
            to_email=to_email,
        )
        return message


class EmailMessageSender(object):

    def __init__(self, email_message):
        self.email_message = email_message

    def send(self):
        django_message = DjangoEmailMessage(
            self.email_message.subject,
            self.email_message.body,
            self.email_message.sender_email,
            [self.email_message.to_email]
        )
        try:
            django_message.send()
            self.email_message.mark_sent()
        except Exception as e:
            self.email_message.mark_error(str(e))
