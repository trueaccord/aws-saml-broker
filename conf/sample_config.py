from config_helper import default_saml_settings

CONFIG = {
  # Creates a SAML settings configuration, assuming your metadata file is
  # given here.
  'saml_settings': default_saml_settings('conf/metadata.xml'),

  # SAML attribute that contains the username. Used for setting the session
  # name in AWS.
  'username_attribute': 'email',

  # SAML attribute that contains the group memberships of the user.
  'group_attribute': 'groups',

  # Maps a group the user belongs to a AWS role arn.
  'group_to_aws_role': {
      # 'group1': 'arn:aws:iam::....:role/RoleName',
  },

  'aws_region': 'us-west-2',

  # Credentials of an AWS user who can AssumeRole for the above roles.
  # You can leave None and have Boto pick up values from the environment:
  # variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
  'aws_access_key_id': None,
  'aws_secret_access_key': None,

  # Uncomment the Okta section if you want to enable a programmatic API
  # to authenticate with Okta and get groups.
  # 'okta': {
  #     'api_token': '...'
  #     'domain': 'yourdomain.okta.com',
  # }
}
