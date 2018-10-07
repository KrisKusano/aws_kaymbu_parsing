"""
Run full lambda pipeline for one s3 item.

Useful for reprocessing a failed email
"""
import argparse
from lambda_function import lambda_worker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Process an s3 email and update simpledb"
    )
    parser.add_argument('bucket', help='Bucket name')
    parser.add_argument('key', help='Name of object')
    args = parser.parse_args()

    lambda_worker(args.bucket, args.key)
