import email
import json
import subprocess
from datetime import datetime as dt
from unittest import TestCase

import boto3
import pytz

from lambda_function import lambda_handler, lambda_worker
from note_parse import parse_gretchens_notes, parse_gretchens_picture


def _load_email(test_path: str) -> str:
    with open(test_path, 'r') as test_file:
        mail = email.message_from_file(test_file)
    return mail.get_payload(decode=True).decode('utf-8')


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

    def test_weekly_picture(self):
        """
        Download an image from their server

        Note: I do not know when the image link in this emai lwill expire and
        thus make this test fail...
        """
        mail = _load_email('test_weekly_picture')
        output = parse_gretchens_picture(mail)
        # one media item found
        self.assertEqual(1, len(output))
        # image name extracted from header correctly
        self.assertEqual('5bca27da361b5d0014939f80.jpg',
                         output[0][1].result)
        # non-zero image content
        self.assertGreater(len(output[0][0]), 0)

    def test_weekly_picture_worker(self):
        bucket = 'gretchens-house-emails'
        key = 'test_weekly_picture'
        activities, _ = lambda_worker(bucket, key)

        # check object was put in s3 recently
        s3 = boto3.client('s3')
        out_file = activities[0].result
        obj_info = s3.head_object(
            Bucket=bucket,
            Key='media/{}'.format(out_file)
        )
        mod_diff = obj_info['LastModified'] - dt.now().astimezone(pytz.utc)
        self.assertLess(mod_diff.total_seconds(),
                        60)

        # check it is in simpledb
        sdb = boto3.client('sdb')
        query_str = 'select * from `gretchens-notes-db` where ' + \
                    'activity = "Media" and result = "{}"'
        res = sdb.select(
            SelectExpression=query_str.format(out_file)
        )
        self.assertTrue('Items' in res)
        self.assertEqual(1, len(res['Items']))
