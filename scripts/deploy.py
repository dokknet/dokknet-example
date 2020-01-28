#!/usr/bin/env python3
"""Build and deploy static site to S3 website hosting.

Uses AWS region from ambient configuration (environment variable or AWS cli
config file).

Cloudformation create/update based on:
https://gist.github.com/svrist/73e2d6175104f7ab4d201280acba049c
"""
import argparse
from datetime import datetime
import json
import logging
import subprocess

import boto3
from botocore.exceptions import ClientError

from build import build


def build_and_deploy(domain, stack_name, template_file, site_dir, cache_age):
    build(site_dir)
    return deploy(domain, stack_name, template_file, site_dir, cache_age)


def deploy(domain, stack_name, template_file, site_dir, cache_age):
    params = [{'ParameterKey': 'DomainName', 'ParameterValue': domain}]
    outputs = create_update_stack(stack_name, template_file, params)
    website_url = get_output_value(outputs, 'WebsiteURL')
    sync_site_to_s3(site_dir, domain, cache_age)
    subprocess.run(['wrangler', 'publish'], cwd='./cf-worker', check=True)
    return website_url


def get_output_value(outputs, key):
    try:
        return next(o['OutputValue'] for o in outputs if key == o['OutputKey'])
    except StopIteration:
        raise KeyError


def sync_site_to_s3(site_dir, bucket_name, cache_age):
    logging.info(f'Uploading site dir: {site_dir} to bucket: {bucket_name}')
    # Boto3 doesn't have s3 sync functionality
    cmd = f'aws s3 sync {site_dir} s3://{bucket_name} ' \
          f'--cache-control max-age={cache_age}'
    subprocess.run(cmd.split(' '), check=True)


def create_update_stack(stack_name, template_file, parameters):
    """Create or update Cloudformation stack."""
    cf = boto3.client('cloudformation')

    template_data = parse_template(cf, template_file)

    params = {
        'StackName': stack_name,
        'TemplateBody': template_data,
        'Parameters': parameters,
    }

    try:
        if stack_exists(cf, stack_name):
            logging.info('Updating {}'.format(stack_name))
            cf.update_stack(**params)
            waiter = cf.get_waiter('stack_update_complete')
        else:
            logging.info('Creating {}'.format(stack_name))
            cf.create_stack(**params)
            waiter = cf.get_waiter('stack_create_complete')
        logging.info('...waiting for stack to be ready...')
        waiter.wait(StackName=stack_name)
    except ClientError as e:
        error_message = e.response['Error']['Message']

        if error_message == 'No updates are to be performed.':
            logging.info(error_message)
        else:
            raise e

    stack_description = cf.describe_stacks(StackName=stack_name)
    logging.info(json.dumps(
        stack_description,
        indent=2,
        default=json_serial
    ))
    return stack_description['Stacks'][0]['Outputs']


def parse_template(cf, template):
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cf.validate_template(TemplateBody=template_data)
    return template_data


def stack_exists(cf, stack_name):
    stacks = cf.list_stacks()['StackSummaries']
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if stack_name == stack['StackName']:
            return True
    return False


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--domain', type=str, required=True,
                        help='Domain name of the site.')
    parser.add_argument('-s', '--site_dir', type=str,
                        default='./site',
                        help='Directory to build the site to')
    parser.add_argument('-n', '--stack_name', type=str,
                        default='DokknetExampleIntegration',
                        help='Cloudformation stack name')
    parser.add_argument('-t', '--template_file', type=str,
                        default='./cloudformation/website.yml',
                        help='Cloudformation template file')
    parser.add_argument('-c', '--cache_age', type=int,
                        default=3600,
                        help='Max cache age of files in seconds')
    args = parser.parse_args()

    website_url = build_and_deploy(args.domain,
                                   args.stack_name,
                                   args.template_file,
                                   args.site_dir,
                                   args.cache_age)
    logging.info(f'\n+++ Successfuly deployed website {args.domain} +++')
