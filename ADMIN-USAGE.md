# Using Admin interface to setup and run a job
This is starting from an empty database with a superuser.

http://10.109.253.90:8000 is the internal address for a testing version of bespin.

If you are running this locally you will need to change this value below.

## Setup Credentials

This will allow bespin to access DukeDS on your behalf for downloading and uploading files.

### Create DukeDS application credential:
http://10.109.253.90:8000/admin/data/ddsapplicationcredential/

Click add dds applicatin credential

The Agent key field comes from the 'Software Agent API Key' field in a DukeDS agent https://dataservice.duke.edu/#/agents
The Api root should be set to 'https://api.dataservice.duke.edu/api/v1'.

This step may already be done if there is a DDS application credential already.

### Create your DukeDS user credential:
http://10.109.253.90:8000/admin/data/ddsusercredential/

Click add dds user credential.

Pick your user in the dropdown.

For token go back to an agent at https://dataservice.duke.edu/#/agents

Click three dots, Click user Secret Key, Click copy key to clipboard

Paste this value into the token field.

## Setup a workflow
We will add a CWL workflow to the database.

### Create a workflow
http://10.109.253.90:8000/admin/data/workflow/

Click Add Workflow

Enter some name for the workflow

Click Save


### Create a workflow version
http://10.109.253.90:8000/admin/data/workflowversion/

Click Add Workflow Version

Pick your workflow from earlier

Specify object name "#main" is typically what you will need.

For Version enter "1"

For Url you will need to reference a cwl workflow created with the "--pack" option.

You will need to consult the CWL workflow to determine the inputs and outputs.

## Setup a job
We will create a job in the database for your user.

### Create a job
http://10.109.253.90:8000/admin/data/job/

Click add job

Pick the version of the workflow you wish to run

Pick your user

Leave state at New

Set vm flavor to 'm1.small'

Set vm instance to '.'

The last two could be left blank but admin interface currently requires them.


## Request a job to be run




