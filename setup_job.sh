#!/usr/bin/env bash
# Tests out the end user API.
# Creates a job with some input files.
# Assumes you are already running the webserver.
# You must setup a workflow version in the admin interface (http://127.0.0.1:8000/admin/ ) before running this script.
# You should fill in the TOKEN with a auth token created through the admin interface.

set -e
# bespin-api token
TOKEN='FILL_ME_IN'
# bespin-api url
BASE_URL=http://127.0.0.1:8000/api

AUTH_HEADER="Authorization: Token $TOKEN"
JSON_CONTENT_HEADER="Content-Type: application/json"

if [ "$TOKEN" == "FILL_ME_IN" ]
then
   echo "First fill in TOKEN at the top of setup_job.sh."
   exit 1
fi

#You will need to hard code USER_CRED_ID after the first time you run this
echo "Create DDS user credential"
PAYLOAD='{"token":"abc","endpoint":1}'
USER_CRED_ID=$(curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/dds-user-credentials/ | sed -e 's/..id..//' -e 's/,.*//')
echo "DDS user credential $USER_CRED_ID"

echo "Create job"
PAYLOAD='{"workflow_version":1,"name":"Predictions for chr1", "workflow_input_json":"{}", "vm_flavor":"m1.xlarge", "vm_project_name":"bespinuser1"}'
JOB_ID=$(curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/jobs/ | sed -e 's/..id..//' -e 's/,.*//')
echo "Create job $JOB_ID"

echo "Create job output directory"
PAYLOAD="{\"job\":$JOB_ID, \"dir_name\":\"Results-Dec-22\", \"project_id\":\"123\", \"dds_user_credentials\":$USER_CRED_ID}"
curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/job-output-dirs/

echo "Create job input file"
PAYLOAD="{\"job\":$JOB_ID, \"file_type\":\"dds_file\", \"workflow_name\":\"model\"}"
JOB_INPUT_ID=$(curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/job-input-files/ | sed -e 's/..id..//' -e 's/,.*//')
echo "Created job input file $JOB_INPUT_ID"

echo "Create dds job input file"
PAYLOAD="{\"job_input_file\":$JOB_INPUT_ID, \"project_id\":\"321\", \"file_id\":\"112\", \"dds_user_credentials\":$USER_CRED_ID, \"destination_path\":\"file.txt\", \"index\":1}"
curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/dds-job-input-files/

echo "Create url job input file"
PAYLOAD="{\"job_input_file\":$JOB_INPUT_ID, \"url\":\"http://stuff\", \"destination_path\":\"file2.txt\", \"index\":1}"
curl -s -H "$AUTH_HEADER" -H "$JSON_CONTENT_HEADER" -X POST -d "$PAYLOAD" $BASE_URL/url-job-input-files/
