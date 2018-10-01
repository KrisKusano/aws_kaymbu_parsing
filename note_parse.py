import re
from collections import namedtuple
from datetime import datetime
import pytz
from typing import List, Tuple


Activity = namedtuple('Activity', ['first_name',
                                   'date',
                                   'activity',
                                   'datetime',
                                   'result',
                                   'notes'])


Nap = namedtuple('Nap', ['first_name',
                         'start_datetime',
                         'end_datetime'])


def parse_gretchens_notes(email_payload: str
                          ) -> Tuple[List[Activity], List[Nap]]:
    """
    Parse out name, date, and activities from email
    :param email_payload: string of HTML email
    :return: attributes
    """
    print('start parsing email')
    # TODO: Find a clever way to detect time zone
    time_zone = pytz.timezone('US/Eastern')

    # remove line breaks put in my gmail
    payload = re.sub('=(\r\n|\r|\n)', '', email_payload)
    # do not allow line breaks within messages
    payload = re.sub('(\r\n|\r|\n)', ' ', payload)

    # get document attributes
    child_name_re = re.search("class=3D\"heading-name\">(.*)'s Daily Note<",
                              payload)
    if child_name_re:
        child_name = child_name_re.group(1)
    else:
        raise ValueError("Could not find child's name")

    date_re = re.search("class=3D\"heading-date\">(.*?)<",
                        payload)
    if date_re:
        date_str = re.sub('(rd|st|th)', '', date_re.group(1))
        date_py = datetime.strptime(date_str, '%B %d, %Y')
        date = date_py.strftime('%Y-%m-%d')
    else:
        raise ValueError("Could not find date")

    # get activities and notes
    act_split = payload.split('class=3D"activity-middle activity-name">')
    re_begin = re.compile("^(.*?)</td>")
    re_result = re.compile("class=3D\"activity-middle activity-result\">"
                           "(.*?)</td>")
    re_note = re.compile("class=3D\"activity-middle activity-notes\">"
                         "(.*?)</td>")
    activities = []
    for act_str in act_split[1:]:
        activity_name = re_begin.search(act_str).group(1)
        print('ACTIVITY:', activity_name)

        # remove out unwanted stuff
        act_str = re_begin.sub('', act_str)
        act_str = act_str.replace('</body></html>', '')

        if activity_name.lower() != 'note':

            act_sub_split = act_str.split(
                "class=3D\"activity-left activity-time\">"
            )
            for act_sub in act_sub_split[1:]:
                time_str = re_begin.search(act_sub).group(1)
                # parse this time
                py_time = datetime.strptime(time_str, '%I:%M%p')
                if date_py is None:
                    e_str = 'Activity time found before date?'
                    raise ValueError(e_str)
                activity_time = _make_iso_time(py_time,
                                               date_py,
                                               time_zone)
                print('Activity time:', activity_time)
                # result
                activity_result = re_result.search(act_sub).group(1)
                print('Activity result:', activity_result)
                activity_note_re = re_note.search(act_sub)
                if activity_note_re:
                    activity_note = activity_note_re.group(1)
                    print('Activity note:', activity_note)
                else:
                    activity_note = None

                activities.append(Activity(first_name=child_name,
                                           date=date,
                                           activity=activity_name,
                                           datetime=activity_time,
                                           result=activity_result,
                                           notes=activity_note))

        else:
            # notes are split by result, not time
            act_sub_split = act_str.split(
                "class=3D\"activity-middle activity-result\">"
            )
            activity_time = None
            for act_sub in act_sub_split[1:]:
                activity_result = re_begin.search(act_sub).group(1)
                print('Note result:', activity_result)
                activity_note_re = re_note.search(act_sub)
                if activity_note_re:
                    activity_note = activity_note_re.group(1)
                    print('Note note:', activity_note)
                else:
                    activity_note = None
                activities.append(Activity(first_name=child_name,
                                           date=date,
                                           activity=activity_name,
                                           datetime=activity_time,
                                           result=activity_result,
                                           notes=activity_note))

        print('---')

    # parse naps
    re_nap = re.compile('([0-9]+:[0-9]+ (AM|PM)) - ([0-9]+:[0-9]+ (AM|PM))')
    naps = []
    for act in activities:
        if act.activity.upper() == 'NAP':
            re_nap_search = re_nap.search(act.result)
            if re_nap_search is None:
                e_str = 'No nap time found in string: {}'.format(act.result)
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
