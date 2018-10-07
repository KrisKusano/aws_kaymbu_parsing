import urllib.parse
from typing import List

import boto3

from note_parse import parse_gretchens_notes, Activity, Nap
from sdb_modify_domain import SDB_DOMAIN

print('Loading function')

s3 = boto3.client('s3')
sdb = boto3.client('sdb')


def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'],
                                    encoding='utf-8')
    lambda_worker(bucket, key)


def lambda_worker(bucket: str, key: str) -> None:
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        # print("CONTENT TYPE: " + response['ContentType'])
        # return response['ContentType']
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}.'.format(key, bucket))
        raise e

    # Parse email for activities
    body = response['Body'].read()
    try:
        activities, naps = parse_gretchens_notes(body.decode('utf-8'))
    except Exception as e:
        print(e)
        print('Error parsing activities out of email')
        raise e

    # put in SimpleDB
    try:
        put_sdb_activities(sdb, activities, naps)
    except Exception as e:
        print(e)
        print('Error while putting data in SimpleDB')
        raise e


def put_sdb_activities(sdb: boto3.client,
                       activities: List[Activity],
                       naps: List[Nap]) -> None:
    act_counts = {}
    for act in activities:
        act_id = '-'.join(act[:3])
        act_counts[act_id] = act_counts.setdefault(act_id, -1) + 1

        # store all activities
        attributes = [
                {
                    'Name': 'first_name',
                    'Value': act.first_name,
                    'Replace': True
                },
                # {
                #     'Name': 'date',
                #     'Value': act.date,
                #     'Replace': True
                # },
                {
                    'Name': 'activity',
                    'Value': act.activity,
                    'Replace': True
                },
                {
                    'Name': 'result',
                    'Value': act.result,
                    'Replace': True
                }
        ]
        if act.notes:
            attributes.append({
                'Name': 'notes',
                'Value': act.notes,
                'Replace': True
            })
        if act.datetime:
            attributes.append({
                'Name': 'start_datetime',
                'Value': act.datetime,
                'Replace': True
            })

        if act_counts[act_id] > 99:
            e_str = 'Activity count over 99 for id {}, zero padding will fail'
            raise ValueError(e_str.format(act_id))

        sdb.put_attributes(
            DomainName=SDB_DOMAIN,
            ItemName='-'.join([act_id, str(act_counts[act_id]).zfill(3)]),
            Attributes=attributes
        )

    nap_count = 0
    for nap in naps:
        attributes = [
            {
                'Name': 'first_name',
                'Value': nap.first_name,
                'Replace': True
            },
            {
                'Name': 'activity',
                'Value': 'NapTimes',
                'Replace': True
            },
            {
                'Name': 'start_datetime',
                'Value': nap.start_datetime,
                'Replace': True
            },
            {
                'Name': 'end_datetime',
                'Value': nap.end_datetime,
                'Replace': True
            }
        ]

        if nap_count > 99:
            e_str = 'over 99 naps, ID zero padding will fail'
            raise ValueError(e_str)
        nap_id = '-'.join([nap.first_name,
                           # date
                           nap.start_datetime[:10],
                           'NapTimes',
                           str(nap_count).zfill(3)])
        sdb.put_attributes(
            DomainName=SDB_DOMAIN,
            ItemName=nap_id,
            Attributes=attributes
        )
        nap_count += 1
