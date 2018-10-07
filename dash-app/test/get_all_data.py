"""
Get unit test data
"""
import json
from datetime import datetime

import boto3

from sdb_modify_domain import SDB_DOMAIN

if __name__ == '__main__':
    today_str = datetime.now().strftime('%Y-%m-%d')
    out_name = today_str + '-data.json'

    sdb = boto3.client('sdb')
    next_token = ''
    out_data = None
    while True:
        res = sdb.select(
            SelectExpression='select * from `{}`'.format(SDB_DOMAIN),
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

    with open(out_name, 'w') as out_file:
        json.dump(res, out_file)
