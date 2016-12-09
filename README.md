# bespin-workflows
Web application for running workflows in the cloud

Currently a very bare-bones django application.

    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt
    $ python manage.py migrate
    $ python manage.py createsuperuser
    $ python manage.py runserver

## View DukeDS Projects

1. Visit http://localhost:8000/admin. Login with your superuser account
2. Create a __DDSApplicationCredential__ with an agent key and DukeDS API root URL.
3. Create a __DDSUserCredential__ object with a user key as the token
4. Visit http://localhost:8000/api/ and click the projects link

## Creating/Running a job.
1. Visit http://localhost:8000/admin. Login with your superuser account
2. Create a __Workflow__ with some name.
3. Create a __WorkflowVersion__ for your __Workflow__ specifying a url to a packed cwl workflow.
4. Create a __Job__ for your WorkflowVersion specifying input json for your cwl workflow.
5. Create an __Job input file__ for each File input parameter in your cwl workflow
6. Create __Url job input file__ or __Dds job input file__ for each input file.
7. Create a __Job output dir__ for your job so the results can be saved.
8. Create a __Lando connection__ so we can talk to a running https://github.com/Duke-GCB/lando instance.
9. Visit http://localhost:8000/api/jobs/1/start, Click POST
