import re
import dateutil.parser
from datetime import datetime
from typing import Dict, List
import logging


def get_logger():
    return logging.getLogger("get_data")


def _get_item_by_activity(items: List[Dict],
                          activity: str) -> List[Dict]:
    """
    Select items that match (not case sensitive) an activity name
    :param items: item list
    :param activity: activity name
    :return:
    """
    items_out = []
    for item in items:
        for atrib in item['Attributes']:
            if atrib['Name'] == 'activity':
                if atrib['Value'].upper() == activity.upper():
                    items_out.append(item)
                break
    return items_out


def _update_date(date1: datetime, date2: datetime) -> datetime:
    """
    Update date1 with (year, month, day) in date2
    """
    return date1.replace(year=date2.year,
                         month=date2.month,
                         day=date2.day)


def compute_nap_times(items: List[Dict]) -> Dict[str, float]:
    """
    Compute nap times from activity list

    :param items: database items
    :return:
    """
    re_nap = re.compile('\(([0-9]*:[0-9]*\s*(AM|PM))\s*-'
                        '\s*([0-9]*:[0-9]*\s*(AM|PM))\)')
    night_fstr = '%I:%M %p'
    nap_out = []
    for nap in _get_item_by_activity(items, 'Nap'):
        start_time = None
        for atrib in nap['Attributes']:
            if atrib['Name'] == 'result':
                re_nap_res = re_nap.search(atrib['Value'])
                if re_nap_res:
                    nap_start = datetime.strptime(re_nap_res.group(1),
                                                  night_fstr)
                    nap_end = datetime.strptime(re_nap_res.group(3),
                                                night_fstr)
                else:
                    f_str = "Could not find nap time from string '{}'"
                    get_logger().info(f_str.format(atrib['Value']))
            elif atrib['Name'] == 'start_datetime':
                start_time = dateutil.parser.parse(atrib['Value'])

        if not start_time:
            f_str = 'No start_datetime attribute: {}'
            get_logger().info(f_str.format(nap))
            continue

        nap_start = _update_date(nap_start, start_time)
        nap_end = _update_date(nap_end, start_time)
        nap_diff = nap_end - nap_start

        nap_out.append((nap_start,
                        nap_diff.days * 24 * 3600 + nap_diff.seconds))

    # remove duplicate nap entries (can happen by mistaken entry)
    nap_out = list(set(nap_out))

    return sorted(nap_out)
