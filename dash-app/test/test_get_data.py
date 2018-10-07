import json
import os
from unittest import TestCase
import dateutil.parser
from datetime import datetime
import re

from get_data import compute_nap_times


class TestGetData(TestCase):
    def setUp(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        test_data_path = os.path.join(this_dir, 'test_data.json')
        with open(test_data_path, 'r') as test_file:
            self.data = json.load(test_file)

        date_start = datetime(2018, 10, 1)
        date_end = datetime(2018, 10, 6)
        self.week_data = {'Items': []}
        re_date = re.compile("^.*-([0-9]{4}-[0-9]{2}-[0-9]{2})-.*$")
        for item in self.data['Items']:
            item_date_str = re_date.search(item['Name']).group(1)
            item_date = datetime.strptime(item_date_str,
                                          '%Y-%m-%d')
            if date_start <= item_date <= date_end:
                self.week_data['Items'].append(item)

    def testNapDurations(self):
        compute_nap_times(self.week_data['Items'])
