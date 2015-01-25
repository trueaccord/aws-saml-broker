#!/usr/bin/env python

from flask import Flask
from flask import request, redirect, Response
import argparse
import base64
import json
import requests
import saml2
import saml2.client
import saml2.config
import boto
import boto.exception
from boto import sts


app = Flask(__name__)


def _attribute_values_by_name(authn, name):
    for attr in authn.assertion.attribute_statement[0].attribute:
        if attr.name == name:
            values = [v.text for v in attr.attribute_value]
            return values
    else:
        raise KeyError('Attribute not found')


def find_aws_role(groups):
    group_mapping = CONFIG['group_to_aws_role']
    for group in groups:
        if group in group_mapping:
            return group_mapping[group]
    else:
        return None


def get_credentials_for(role_arn):
    conn = sts.connect_to_region(
        CONFIG.get('aws_region'),
        aws_access_key_id = CONFIG.get('aws_access_key_id'),
        aws_secret_access_key = CONFIG.get('aws_secret_access_key'))
    if conn is None:
        return 'Could not get connection', 500
    try:
        c = conn.assume_role(
          role_arn = role_arn,
          role_session_name = 'Moshic')
    except boto.exception.BotoServerError, e:
        return 'AssumeRole failed.', 401
    return print_aws_config(c.credentials)


def print_aws_config(creds):
    return Response("""[default]
# Will expire on %s
aws_access_key_id = %s
aws_secret_access_key = %s
aws_session_token = %s
""" % (creds.expiration, creds.access_key, creds.secret_key, creds.session_token), mimetype='text/plain')


@app.route("/", methods=['GET', 'POST'])
def index():
    resp = request.form.get('SAMLResponse')
    if not resp:
        (req_id, authn) = saml_client.prepare_for_authenticate()
        return redirect(authn['url'])

    authn = saml_client.parse_authn_request_response(
        resp, saml2.BINDING_HTTP_POST)
    try:
        user = _attribute_values_by_name(authn, CONFIG['username_attribute'])
    except KeyError:
        return 'User attribute could not be found in SAML.', 400
    if len(user) != 1:
        return 'User attribute contained more than one value.', 400

    group_attribute = CONFIG['group_attribute']
    try:
        groups = _attribute_values_by_name(authn, group_attribute)
    except KeyError:
        return 'Group attribute was not found in SAML.', 400

    if not groups:
        return 'No SAML groups found in SAML.', 400
    aws_role = find_aws_role(groups)
    if aws_role is None:
        return 'Could not find an AWS role for group memberships', 400

    return get_credentials_for(aws_role)


def read_config(filename):
    ns = {}
    execfile(filename, ns)
    return ns['CONFIG']


def create_client():
    config = saml2.config.SPConfig()
    config.load(CONFIG['saml_settings'])
    saml_client = saml2.client.Saml2Client(config)
    return saml_client


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", help="Turns on debug mode (default: false)",
                   action="store_true")
    parser.add_argument(
        "--bind_host", help="Host/IP to bind.")

    parser.add_argument(
        "--config", help="Path to config file", default='conf/config.py')

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    CONFIG = read_config(args.config)
    saml_client = create_client()

    app.debug = args.debug
    app.run(host=args.bind_host)

