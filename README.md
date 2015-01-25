aws-saml-broker
===============

Simple webapp that authenticates users over SAML and grants them temporary AWS
credentials based on SAML attributes.

Building
--------

Building is based on a Dockerfile, however it should be straightforward to 
to install locally by inspecting the Dockerfile.

   $ docker build -t aws-saml-broker .

Configuring
-----------

### Creating a gateway user

In AWS IAM console, create a new user, and download his AWS credentials.
Click on the newly created user, choose 'Attach User Policy', select 'Custom
Policy'. Name it `broker-policy` and set it to:


    {"Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "iam:ListRoles",
          "sts:AssumeRole"
        ],
        "Resource": "*"
      }
    ]}

Note from the User Summary the ARN of this user.

### Create roles for your users

Create as many roles as you need for your users with the permission policy
that you need. For each role, edit the trust relationship to include the
gateway user. The principal section should be:

      "Principal": {
        "AWS": "arn:aws:iam::your-gateway-user"
      },

For each role you create, note its ARN.

### Setting conf/config.py

Save `conf/sample_config.py` as `conf/config.py' and edit accordingly to the
instuctions in the file.

Your SAML metadata xml file should be in `conf/metadata.xml` (can be
customized in the config)

The AWS access key and secret correspond to the gateway user.
`group_to_aws_role` maps SAML groups to the ARNs of the roles you crate in the
previous step.

### Setting up Okta as an identity provider

aws-saml-broker works with any Identity Provider that speaks SAML. This section explains
how to configure Okta to work with aws-saml-broker.

In Okta, add a new app using the 'Template SAML 2.0 App'. Set the Post Back URL to
the URL the app will be serving from.  If you are testing locally, enter
`http://localhost:5000`.

Set *Attribute Statements* to `email|${user.email}`

Set *Group Name* to `groups`, and if you would like to filter your groups by
some regular expression, enter it in *Group Filter*

Create the application and assign it people and/or groups.  From the `Sign On`
page download the _Identity Provider metadata_ and save it in
`conf/metadata.xml`.

### Starting the webapp

    docker run --rm -p 5000:5000 -v $PWD/conf:/server/conf aws-saml-broker

Visit http://localhost:5000/ and if it all works temporary credentials should
appear on the screen (in a format suitable to pasting in ~/.aws/credentials
for AWS CLI)


