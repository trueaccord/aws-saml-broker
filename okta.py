import requests
import json


class OktaException(Exception):
    pass


def validate_user(okta_config, username, password):
    r = requests.post('https://%s/api/v1/authn' % okta_config['domain'], data=json.dumps({
        'username': username,
        'password': password}),headers={
        'Content-Type': 'application/json',
        'Authorization': 'SSWS %s' % okta_config['api_token']
        })
    r = r.json()

    if r.get('status') != 'SUCCESS':
        raise OktaException('Login failed: %s' % r.get('errorSummary'))

    user_id = r['_embedded']['user']['id']
    return r['_embedded']['user']['profile']['login'], user_id


def get_groups(okta_config, user_id):
    r = requests.get(
        'https://%s/api/v1/users/%s/groups' % (okta_config['domain'], user_id),
         headers={
             'Content-Type': 'application/json',
             'Authorization': 'SSWS %s' % okta_config['api_token']
        }).json()
    return [g['profile']['name'] for g in r]
