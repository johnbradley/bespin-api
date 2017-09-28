from django.test import TestCase
from mailer import EmailMessageFactory, EmailMessageSender
from models import EmailMessage, EmailTemplate
from mock import MagicMock, patch
from exceptions import EmailException

class EmailMessageFactoryTestCase(TestCase):

    def setUp(self):
        self.email_template = EmailTemplate.objects.create(
            name='template1',
            body_template='Body {{ field1 }}',
            subject_template='Subject {{ field2}}',
        )
        self.context = {
            'field1': 'abc',
            'field2': 'def'
        }
        self.sender_email = 'sender@example.com'
        self.to_email = 'recipient@university.edu'

    def test_makes_message(self):
        factory = EmailMessageFactory(self.email_template)

        message = factory.make_message(
            self.context,
            self.sender_email,
            self.to_email
        )

        self.assertEqual(message.body, 'Body abc')
        self.assertEqual(message.subject, 'Subject def')
        self.assertEqual(message.sender_email, self.sender_email)
        self.assertEqual(message.to_email, self.to_email)


class EmailMessageSenderTestCase(TestCase):

    def setUp(self):
        self.subject = 'Message Subject'
        self.body = 'Message Body'
        self.sender_email = 'sender@example.com'
        self.to_email = 'recipient@university.edu'

        self.email_message = EmailMessage.objects.create(
            body=self.body,
            subject=self.subject,
            sender_email=self.sender_email,
            to_email=self.to_email
        )

    @patch('data.mailer.DjangoEmailMessage')
    def test_sends_email(self, MockDjangoEmailMessage):
        mock_send = MagicMock()
        MockDjangoEmailMessage.return_value.send = mock_send
        sender = EmailMessageSender(self.email_message)
        sender.send()
        self.assertEqual(self.email_message.state, EmailMessage.MESSAGE_STATE_SENT)
        self.assertEqual(mock_send.call_count, 1)
        self.assertTrue(mock_send.call_args(self.subject, self.body, self.sender_email, [self.to_email],))

    @patch('data.mailer.DjangoEmailMessage')
    def test_captures_errors_on_send(self, MockDjangoEmailMessage):
        mock_send = MagicMock()
        mock_send.side_effect = Exception('Email error')
        MockDjangoEmailMessage.return_value.send = mock_send
        sender = EmailMessageSender(self.email_message)
        with self.assertRaises(EmailException):
            sender.send()
        self.assertEqual(self.email_message.state, EmailMessage.MESSAGE_STATE_ERROR)
        self.assertEqual(self.email_message.errors, 'Email error')
        self.assertEqual(mock_send.call_count, 1)
        self.assertTrue(mock_send.call_args(self.subject, self.body, self.sender_email, [self.to_email],))
