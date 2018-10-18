import html as py_html
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import boto3
import dash_html_components as html
import dateutil.parser
import pandas as pd


sdb = boto3.client('sdb')


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


def compute_nap_times(items: List[Dict]) -> List[Tuple[datetime, float]]:
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
        nap_start, nap_end = None, None
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

        if nap_start and nap_end:
            nap_start = _update_date(nap_start, start_time)
            nap_end = _update_date(nap_end, start_time)
            nap_diff = nap_end - nap_start
            nap_min = nap_diff.days * 24 * 3600 + nap_diff.seconds
        else:
            nap_min = float('nan')

        nap_out.append((nap_start, nap_min))

    # remove duplicate nap entries (can happen by mistaken entry)
    nap_out = list(set(nap_out))

    return sorted(nap_out)


def df_from_items(items: List[Dict]) -> pd.DataFrame:
    """
    Table from item list
    """
    rows_out = []
    for item in items:
        try:
            rows_out.append({x['Name']: x['Value'] for x in item['Attributes']})
        except (TypeError, KeyError):
            logging.debug('Malformed items list: {}'.format(items))
            break
    return pd.DataFrame(rows_out)


def html_table_from_df(df: pd.DataFrame) -> html.Table:
    return html.Table(
        [html.Tr([html.Th(col) for col in df.columns])] +
        [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
         for i in range(len(df))]
    )


def get_activty_table(items: List[Dict]) -> html.Table:
    df = df_from_items(_get_item_by_activity(items,
                                             'Activity'))
    df['Date'] = df['start_datetime'].apply(
        lambda x: dateutil.parser.parse(x).strftime('%Y-%m-%d %H:%M %p')
    )
    df['Topic'] = df['result']
    df['Description'] = df['notes'].apply(lambda x: py_html.unescape(x))
    return html_table_from_df(df.loc[:, ['Date', 'Topic', 'Description']])


def get_week_data(date: str) -> Dict:
    """
    Query the weeks worth of data from SimpleDB
    """
    date_fmt = "%Y-%m-%d"
    day = datetime.strptime(date, date_fmt)
    select_cols = ['result', 'activity', 'start_datetime', 'end_datetime',
                   'notes']
    week_start = day - timedelta(days=day.weekday())
    week_end = week_start + timedelta(days=6)
    query_str = 'select {} from `gretchens-notes-db` where ' + \
        '`start_datetime` >= "{}" and `start_datetime` <= "{}"'
    query_str = query_str.format(','.join(select_cols),
                                 week_start.strftime(date_fmt),
                                 week_end.strftime(date_fmt))
    out_data = None
    next_token = ''
    while True:
        res = sdb.select(
            SelectExpression=query_str,
            NextToken=next_token
        )

        if not out_data:
            out_data = res
        else:
            out_data['Items'].extend(res['Items'])

        if 'NextToken' not in res:
            break
        else:
            next_token = res['NextToken']

    if 'NextToken' in out_data:
        del out_data['NextToken']

    return out_data
