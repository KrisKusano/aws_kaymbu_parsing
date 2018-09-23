import email
from unittest import TestCase
from note_parse import parse_gretchens_notes


class TestNoteParse(TestCase):
    def test_note_parse(self):
        test_path = 'test_message'
        with open(test_path, 'r') as test_file:
            mail = email.message_from_file(test_file)
        payload = mail.get_payload()
        activities_list = parse_gretchens_notes(payload)
        self.assertEqual(7, len(activities_list))
        name = 'Emilia'
        date = '2018-09-21'
        self.assertEqual((name,
                          date,
                          'Meal',
                          '2018-09-21 08:30:00',
                          'Ate all of my breakfast',
                          None),
                         activities_list[0])
        self.assertEqual((name,
                          date,
                          'Diaper',
                          '2018-09-21 16:11:00',
                          'BM diaper',
                          None),
                         activities_list[4])
        self.assertEqual((name,
                          date,
                          'Activity',
                          '2018-09-21 12:15:00',
                          'Outside Time',
                          'Mia and Emilia used markers together outside.  ' +
                          'Emilia signaled "please" before sitting down and ' +
                          'Mia nodded her head.  They both drew on pink ' +
                          'paper. '),
                         activities_list[6])
