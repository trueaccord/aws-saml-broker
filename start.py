#!/usr/bin/env python

from flask import Flask
from flask import request, redirect, Response
import argparse
import base64
import requests
import saml2
import saml2.client
import saml2.config
import boto
import boto.exception
import okta
import json
from boto import sts
import requests


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


def get_credentials_for(session_name, role_arn):
    conn = sts.connect_to_region(
        CONFIG.get('aws_region'),
        aws_access_key_id = CONFIG.get('aws_access_key_id'),
        aws_secret_access_key = CONFIG.get('aws_secret_access_key'))
    if conn is None:
        return 'Could not get connection', 500
    try:
        c = conn.assume_role(
          role_arn = role_arn,
          role_session_name = session_name)
    return c.credentials


FORMATS = {
        'awscli': ('text/plain', lambda c: """[default]
# Will expire on %(expiration)s
aws_access_key_id = %(aws_access_key_id)s
aws_secret_access_key = %(aws_secret_access_key)s
aws_session_token = %(aws_session_token)s""" % c),
        'json': ('application/json', lambda c: json.dumps(c, indent=4))
        }

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

    return response_from_groups(session_name=user, groups=groups, format='awscli')


@app.route("/login/okta", methods=['POST'])
def login_okta():
    okta_config = CONFIG.get('okta')
    format = request.args.get('format', 'json')
    if format not in FORMATS:
        return 'Unsupported format', 400

    if not okta_config:
        return "Okta is not configured.", 400
    username = request.form['username']
    password = request.form['password']
    try:
        email, user_id = okta.validate_user(okta_config, username, password)
        groups = okta.get_groups(okta_config, user_id)
    except okta.OktaException, e:
        return str(e), 401
    return response_from_groups(session_name=email, groups=groups, format=format)


def response_from_groups(session_name, groups, format=format):
    if not groups:
        return 'No groups found.', 400
    aws_role = find_aws_role(groups)
    if aws_role is None:
        return 'Could not find an AWS role for group memberships', 400

    try:
        creds = get_credentials_for(session_name, aws_role)
    except boto.exception.BotoServerError, e:
        return 'AssumeRole failed.', 401

    context = {
            'expiration': creds.expiration,
            'aws_access_key_id': creds.access_key,
            'aws_secret_access_key': creds.secret_key,
            'aws_session_token': creds.session_token
    }
    mime_type, call = FORMATS[format]
    return Response(call(context), mimetype=mime_type)


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

