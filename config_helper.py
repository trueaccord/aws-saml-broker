import saml2

def default_saml_settings(metadata_file):
  return {
    'metadata': {
      'local': [metadata_file]
    },
    'service': {
      'sp': {
        'name': 'AWS Credentials Maker',
        'endpoints': {
          'assertion_consumer_service': ('http://localhost:5000/', saml2.BINDING_HTTP_POST)
        },
        'allow_unsolicited': True,
      }
    },
    'debug': 1,
  }

