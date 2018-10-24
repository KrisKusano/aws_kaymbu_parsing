import os
import re
from collections import namedtuple
from datetime import datetime
from typing import List, Tuple

import pytz
import requests

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

    payload = _remove_line_breaks(email_payload)

    # get document attributes
    child_name_re = re.search("class=\"heading-name\">(.*)'s Daily Note<",
                              payload)
    if child_name_re:
        child_name = child_name_re.group(1)
    else:
        raise ValueError("Could not find child's name")

    date_re = re.search("class=\"heading-date\">(.*?)<",
                        payload)
    if date_re:
        date_str = re.sub('(rd|st|th|nd)', '', date_re.group(1))
        date_py = datetime.strptime(date_str, '%B %d, %Y')
        date = date_py.strftime('%Y-%m-%d')
    else:
        raise ValueError("Could not find date")

    # get activities and notes
    act_split = payload.split('class="activity-middle activity-name">')
    re_begin = re.compile("^(.*?)</td>")
    re_result = re.compile("class=\"activity-middle activity-result\">"
                           "(.*?)</td>")
    re_note = re.compile("class=\"activity-middle activity-notes\">"
                         "(.*?)</td>")
    # (lower case) headings without time
    non_time_headings = ['note', 'supplies']
    activities = []
    for act_str in act_split[1:]:
        activity_name = re_begin.search(act_str).group(1)
        print('ACTIVITY:', activity_name)

        # remove out unwanted stuff
        act_str = re_begin.sub('', act_str)
        act_str = act_str.replace('</body></html>', '')

        if activity_name.lower() not in non_time_headings:

            act_sub_split = act_str.split(
                "class=\"activity-left activity-time\">"
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
                "class=\"activity-middle activity-result\">"
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


def parse_gretchens_picture(email: str) -> List[Tuple[bytes, Activity]]:
    payload = _remove_line_breaks(email)
    re_date = re.compile('class="date">(.*?)</td>')
    re_date_search = re_date.search(payload)
    if re_date_search:
        this_date = re_date_search.group(1)
    else:
        raise ValueError('Could not find date in picture email')

    # time
    time_zone = pytz.timezone('US/Eastern')
    date_raw = datetime.strptime(this_date, "%B %d, %Y")
    date = _make_iso_time(datetime.today(),
                          date_raw,
                          time_zone)

    # find download link
    re_download_link = re.compile(
        '<a href="(.*?)" target=.*><img src=".*/download_btn'
    )
    download_search = re_download_link.search(payload)
    if download_search:
        download_url = download_search.group(1)
        print('Found download link')
    else:
        raise ValueError("Could not find download link in picture email")

    download_page = requests.get(download_url)
    if download_page.status_code != 200:
        raise ValueError('Could not access page at {}'.format(download_url))
    else:
        print('Downloaded page {}'.format(download_url))

    # find media ids
    download_txt = download_page.text
    re_media = re.compile('<div data-type=".*" data-id="(.*?)"')
    media_search = re_media.search(download_txt)
    if not media_search:
        raise ValueError('No media found')

    # download
    base_url = "http://export.kaymbu.com/download/moments?{}&"
    out = []
    for media_id in media_search.groups():
        this_url = base_url.format(media_id)
        media_resp = requests.get(this_url,
                                  stream=True)
        if media_resp.status_code != 200:
            e_str = 'Could not download media file {}'
            raise ValueError(e_str.format(this_url))
        headers = media_resp.headers
        media_name = None
        if 'Content-Disposition' in headers:
            content_split = headers['Content-Disposition'].split(';')
            content_split = [x.strip() for x in content_split]
            if content_split[0] == 'attachment':
                if content_split[1].startswith('filename'):
                    media_name = content_split[1][9:]
        if not media_name:
            print('No media name found in header: {}'.format(headers))

        _, media_ext = os.path.splitext(media_name)
        media_obj_name = media_id + media_ext
        act_info = Activity(first_name=media_obj_name,
                            date=date_raw.strftime('%Y-%m-%d'),
                            activity='Media',
                            datetime=date,
                            result=media_obj_name,
                            notes=media_name
                            )
        out.append((media_resp.content, act_info))
    return out


def _remove_line_breaks(body: str) -> str:
    # remove line breaks
    payload = re.sub('=(\r\n|\r|\n)', '', body)
    # do not allow line breaks within messages
    payload = re.sub('(\r\n|\r|\n)', ' ', payload)
    return payload


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
