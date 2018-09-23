import re
from datetime import datetime
from io import BytesIO
from typing import List, Tuple

from lxml import etree


def parse_gretchens_notes(email_payload: str) -> List[Tuple]:
    """
    Parse out name, date, and activities from email
    :param email_payload: string of HTML email
    :return: attributes
    """
    # remove screwy stuff...
    payload = re.sub('=\n', '', email_payload)

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
                activities.append((child_name,
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
            py_time = py_time.replace(year=date_py.year,
                                      month=date_py.month,
                                      day=date_py.day)
            this_activity_time = py_time.strftime('%Y-%m-%d %H:%M:%S')
        elif attrib_class == '3D"activity-middle' and \
                'activity-result' in elem.attrib:
            this_activity_result = text
        elif attrib_class == '3D"activity-middle' and \
                'activity-notes' in elem.attrib:
            this_activity_notes = text

    # output final
    activities.append((child_name,
                       date,
                       this_activity_name,
                       this_activity_time,
                       this_activity_result,
                       this_activity_notes))
    return activities
