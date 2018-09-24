import re
from collections import namedtuple
from datetime import datetime
from io import BytesIO
import pytz
from typing import List, Tuple

from lxml import etree


Activity = namedtuple('Activity', ['first_name',
                                   'date',
                                   'activity',
                                   'datetime',
                                   'result',
                                   'notes'])


Nap = namedtuple('Nap', ['first_name',
                         'start_datetime',
                         'end_datetime'])


def parse_gretchens_notes(email_payload: str) -> List[Tuple]:
    """
    Parse out name, date, and activities from email
    :param email_payload: string of HTML email
    :return: attributes
    """
    # TODO: Find a clever way to detect time zone
    time_zone = pytz.timezone('US/Eastern')

    # remove screwy stuff...
    payload = re.sub('=(\r\n|\r|\n)', '', email_payload)

    re_name = re.compile("(.*)'s Daily Note")
    child_name = None
    date = None
    doc_string = BytesIO(payload.encode('utf-8'))
    activities = []
    this_activity_name = None
    last_activity_name = None
    this_activity_time = None
    this_activity_result = None
    this_activity_notes = None
    date_py = None
    for event, elem in etree.iterparse(doc_string,
                                       events=("start",),
                                       html=True):
        if elem.tag != 'td' or elem.text is None or 'class' not in elem.attrib:
            continue
        # print('{}: {}'.format(event, elem.text))

        attrib_class = elem.attrib['class']
        text = elem.text
        if attrib_class == '3D"heading-name"':
            re_child_name = re_name.search(text)
            if not re_child_name:
                e_str = 'Could not parse child name from {}'
                raise ValueError(e_str.format(text))
            child_name, = re_child_name.groups()
        elif attrib_class == '3D"heading-date"':
            date_str = re.sub('(rd|st)', '', text)
            date_py = datetime.strptime(date_str, '%B %d, %Y')
            date = date_py.strftime('%Y-%m-%d')
        elif attrib_class == '3D"activity-middle' and \
                'activity-name' in elem.attrib:
            last_activity_name = this_activity_name
            this_activity_name = text
        elif attrib_class == '3D"activity-left' and \
                'activity-time' in elem.attrib:
            # output last activity
            if this_activity_time:
                activities.append(Activity(child_name,
                                           date,
                                           last_activity_name
                                           if last_activity_name is not None
                                           else this_activity_name,
                                           this_activity_time,
                                           this_activity_result,
                                           this_activity_notes))
                this_activity_result = None
                this_activity_notes = None

            # parse this time
            py_time = datetime.strptime(text, '%I:%M%p')
            if date_py is None:
                e_str = 'Activity time found before date?'
                raise ValueError(e_str)
            this_activity_time = _make_iso_time(py_time,
                                                date_py,
                                                time_zone)
        elif attrib_class == '3D"activity-middle' and \
                'activity-result' in elem.attrib:
            this_activity_result = text
        elif attrib_class == '3D"activity-middle' and \
                'activity-notes' in elem.attrib:
            this_activity_notes = text

    # output final
    activities.append(Activity(child_name,
                               date,
                               this_activity_name,
                               this_activity_time,
                               this_activity_result,
                               this_activity_notes))

    # parse naps
    re_nap = re.compile('([0-9]+:[0-9]+ (AM|PM)) - ([0-9]+:[0-9]+ (AM|PM))')
    naps = []
    for act in activities:
        if act.activity.upper() == 'NAP':
            re_nap_search = re_nap.search(act.result)
            if re_nap_search is None:
                e_str = 'No nap time found in string: {}'.format(text)
                raise ValueError(e_str)
            nap_start, nap_end = re_nap_search.group(1), re_nap_search.group(3)
            nap_start_time = _make_iso_time(
                datetime.strptime(nap_start, '%I:%M %p'),
                date_py,
                time_zone
            )
            nap_end_time = _make_iso_time(
                datetime.strptime(nap_end, '%I:%M %p'),
                date_py,
                time_zone
            )
            naps.append(Nap(child_name,
                            nap_start_time,
                            nap_end_time))
    return activities, naps


def _make_iso_time(time: datetime,
                   date: datetime,
                   time_zone: pytz.timezone) -> str:
    """
    Combine time and date and timezone
    :param time: a time (without a date)
    :param date: a date
    :param time_zone: pytz timezone
    :return: iso 8601 time string
    """
    time_combined = time.replace(year=date.year,
                                 month=date.month,
                                 day=date.day)
    return time_zone.localize(time_combined).isoformat()
