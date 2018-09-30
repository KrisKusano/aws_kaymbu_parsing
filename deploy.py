"""
Create deployment package for lambda

Run with environment active so that python will be first thing found on path

This fails to run on lambda because lxml is machine dependent. See deploy.bat
for a working Docker-based workaround.
"""
import boto3
import os
import logging
import re
import shutil
import sys
import zipfile

DEPLOY_NAME = 'deploy'

# files to copy to distribution
SRC_LIST = [
    "lambda_function.py",
    "note_parse.py"
]

def get_logger():
    return logging.getLogger(DEPLOY_NAME)


def clean_deploy(deploy_dir: str) -> None:
    if os.path.exists(deploy_dir):
        f_str = "Deleting temporary deploy directory {}"
        get_logger().info(f_str.format(deploy_dir))
        shutil.rmtree(deploy_dir)


def upload_to_s3(zip_path: str):
    bucket_name = 'gretchens-house-emails'
    get_logger().info('Uploading to S3 bucket {}'.format(bucket_name))
    s3 = boto3.client('s3')
    s3.upload_file(zip_path, bucket_name, os.path.basename(zip_path))


def deploy():
    # set up temp output directory
    this_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.abspath('.') != this_dir:
        f_str = "Run this script from the root directory of the project ({})"
        raise ValueError(f_str.format(this_dir))

    deploy_dir = os.path.join(this_dir, DEPLOY_NAME)
    clean_deploy(deploy_dir)

    # find site packages
    env_dir = os.path.dirname(sys.executable)
    site_package_dir = os.path.join(env_dir, 'Lib', 'site-packages')
    assert os.path.exists(site_package_dir)

    get_logger().info("Copying site packages...")
    shutil.copytree(site_package_dir, deploy_dir)

    # clean up deploy files
    get_logger().info("Cleaning unwanted files out of deploy directory")
    for root_dir, sub_dirs, files in os.walk(deploy_dir):
        if root_dir.endswith('__pycache__') or root_dir.endswith('lxml'):
            if os.path.exists(root_dir):
                shutil.rmtree(root_dir)

    get_logger().info("Copy AWS-compatible lxml")


    get_logger().info("Copying source files...")
    for src_file in SRC_LIST:
        shutil.copy(os.path.join(this_dir, src_file), deploy_dir)

    get_logger().info("Zipping")
    zip_path = os.path.join(this_dir, DEPLOY_NAME + '.zip')
    if os.path.exists(zip_path):
        get_logger().info('Destoying previous {}.zip'.format(DEPLOY_NAME))
    re_str = ''.join(['^', DEPLOY_NAME, '(\\\\|/)'])
    get_logger().info('Making deploy file {}.zip'.format(DEPLOY_NAME))
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for dir_root, sub_dirs, files in os.walk(DEPLOY_NAME):
            # print((dir_root, sub_dirs, files))
            for file in files:
                if dir_root == DEPLOY_NAME:
                    zip_out.write(os.path.join(dir_root, file),
                                  file)
                else:
                    zip_path = os.path.join(re.sub(re_str,
                                                   './',
                                                   dir_root),
                                            file)
                    zip_out.write(os.path.join(dir_root, file),
                                  zip_path)

    upload_to_s3(zip_path)

    get_logger().info('Cleaning up temp directory {}'.format(deploy_dir))
    clean_deploy(deploy_dir)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    deploy()
