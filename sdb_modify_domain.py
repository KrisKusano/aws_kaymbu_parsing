from __future__ import print_function

import argparse

import boto3

SDB_DOMAIN = 'gretchens-notes-db'

def get_args():
    parser = argparse.ArgumentParser('Manipulating my SimpleDB domain')
    parser.add_argument('--create-domain', action='store_true',
                        help='Make domain "{}"'.format(SDB_DOMAIN))
    parser.add_argument('--delete-domain', action='store_true',
                        help='Delete (clear) domain "{}"'.format(SDB_DOMAIN))
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    sdb = boto3.client('sdb')

    response = sdb.list_domains()
    if 'DomainNames' in response and SDB_DOMAIN in response['DomainNames']:
        print('Domain "{}" exists'.format(SDB_DOMAIN))
        if args.delete_domain:
            response = sdb.delete_domain(DomainName=SDB_DOMAIN)
            print('Deleted domain "{}". reponse: {}'.format(SDB_DOMAIN,
                                                            response))

    response = sdb.list_domains()
    if args.create_domain and \
            ('DomainNames' not in response or
             SDB_DOMAIN not in response['DomainNames']):
        response = sdb.create_domain(DomainName=SDB_DOMAIN)
        print('Creating domain "{}", response: {}'.format(SDB_DOMAIN,
                                                          response))
    print('done')
