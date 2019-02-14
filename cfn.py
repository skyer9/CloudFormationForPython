#!/usr/bin/env python

import argparse
import boto
import boto.s3
import boto.cloudformation
from configuration import (
    stack_base_name,
    region_name,
)


def cfn_connect(region_name_to_connect):
    return boto.cloudformation.connect_to_region(region_name_to_connect)


def cfn_update(cfn_conn, stack_name, template_body):
    cfn_conn.update_stack(stack_name, template_body=template_body)


def cfn_create(cfn_conn, stack_name, template_body):
    cfn_conn.create_stack(stack_name, template_body=template_body)


def update(template_name):
    cfn_conn = cfn_connect(region_name)
    stack_name = stack_base_name + '-' + template_name

    if template_name == 'assets':
        print("Updating stack: {0}".format(stack_name))
        from templates import assets as template
        cfn_update(cfn_conn, stack_name, template.get())


def create(template_name):
    cfn_conn = cfn_connect(region_name)
    stack_name = stack_base_name + '-' + template_name

    if template_name == 'assets':
        print("Creating stack: {0}".format(stack_name))
        from templates import assets as template
        cfn_create(cfn_conn, stack_name, template.get())


def parse_args():
    parser = argparse.ArgumentParser(
        description='Creates or updates a CloudFormation stack')
    parser.add_argument('-c', '--create', action='store_true')
    parser.add_argument('-t', '--template',
                        choices=[
                            'assets',
                            'assets_https_enabled',
                        ],
                        required=True,
                        type=str)

    return parser.parse_args()


def main():
    args = parse_args()
    if args.create:
        create(args.template)
        return 0

    update(args.template)
    return 0


if __name__ == "__main__":
    main()