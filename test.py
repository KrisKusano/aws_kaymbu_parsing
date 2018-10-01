import email
import json
import subprocess
from unittest import TestCase

from note_parse import parse_gretchens_notes
from lambda_function import lambda_handler


def _load_email(test_path: str) -> str:
    with open(test_path, 'r') as test_file:
        mail = email.message_from_file(test_file)
    return mail.get_payload()


class TestNoteParse(TestCase):
    def test_note_parse(self):
        test_path = 'test_message'
        payload = _load_email(test_path)
        activities, naps = parse_gretchens_notes(payload)
        self.assertEqual(7, len(activities))
        name = 'Emilia'
        date = '2018-09-21'
        self.assertEqual((name,
                          date,
                          'Meal',
                          '2018-09-21T08:30:00-04:00',
                          'Ate all of my breakfast',
                          None),
                         activities[0])
        self.assertEqual((name,
                          date,
                          'Diaper',
                          '2018-09-21T16:11:00-04:00',
                          'BM diaper',
                          None),
                         activities[4])
        self.assertEqual((name,
                          date,
                          'Activity',
                          '2018-09-21T12:15:00-04:00',
                          'Outside Time',
                          'Mia and Emilia used markers together outside.  ' +
                          'Emilia signaled &quot;please&quot; before sitting ' +
                          'down and Mia nodded her head.  They both drew ' +
                          'on pink paper. '),
                         activities[6])
        self.assertEqual(1, len(naps))
        self.assertEqual((name,
                          '2018-09-21T12:40:00-04:00',
                          '2018-09-21T14:05:00-04:00'),
                         naps[0])

    def test_note_parse2(self):
        """
        A test case that includes a note
        """
        test_path = 'test_message2'
        payload = _load_email(test_path)
        activities, naps = parse_gretchens_notes(payload)

        name = 'Emilia'
        date = '2018-09-13'
        self.assertEqual((name,
                          date,
                          'Note',
                          None,
                          'Picture Day',
                          'Hello I wanted to let everyone know it\'s ' +
                          'picture day on Monday! We are taking group ' +
                          'pictures at 9 and if Monday is not your normal ' +
                          'day you can still come on Monday for pictures.  '
                          'Thank you!=20  '),
                         activities[0])

    def test_lambda_function(self):
        """
        Test local run of lambda function.

        Note: requires access to the S3 resource specified in test_event.json,
        i.e., only me.

        Note: Requires python-lambda-local to be on the path
        """
        subprocess.call(['python-lambda-local',
                         '-f',
                         'lambda_handler',
                         'lambda_function.py',
                         'test_event.json'])

    def test_lambda_function_dummy(self):
        """
        Really run locally
        """
        with open('test_event.json', 'r') as test_event:
            event = json.load(test_event)

        lambda_handler(event, None)
