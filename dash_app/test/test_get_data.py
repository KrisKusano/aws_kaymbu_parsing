import json
import os
from unittest import TestCase
from datetime import datetime
import re

from ..get_data import compute_nap_times, get_activty_table


def get_test_week_data():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    test_data_path = os.path.join(this_dir, 'test_data.json')
    with open(test_data_path, 'r') as test_file:
        data = json.load(test_file)

    date_start = datetime(2018, 10, 1)
    date_end = datetime(2018, 10, 6)
    week_data = {'Items': []}
    re_date = re.compile("^.*-([0-9]{4}-[0-9]{2}-[0-9]{2})-.*$")
    for item in data['Items']:
        item_date_str = re_date.search(item['Name']).group(1)
        item_date = datetime.strptime(item_date_str,
                                      '%Y-%m-%d')
        if date_start <= item_date <= date_end:
            week_data['Items'].append(item)

    return week_data


class TestGetData(TestCase):
    def setUp(self):
        self.week_data = get_test_week_data()

    def testNapDurations(self):
        ans = [
            (datetime(2018, 10, 1, 12, 55),
             3600 + 10 * 60),
            (datetime(2018, 10, 2, 13, 00),
             3600 + 35 * 60),
            (datetime(2018, 10, 3, 12, 55),
             45 * 60),
            (datetime(2018, 10, 4, 13, 00),
             3600 + 15 * 60),
            (datetime(2018, 10, 5, 12, 45),
             3600 + 40 * 60)

        ]
        naps = compute_nap_times(self.week_data['Items'])
        self.assertEqual(ans, naps)

    def testActivityTable(self):
        table = get_activty_table(self.week_data['Items'])
        self.assertEqual(6, len(table.children))
