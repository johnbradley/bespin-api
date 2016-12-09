# bespin-api
Web application for running workflows in the cloud

Currently a very bare-bones django application.

    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt
    $ python manage.py migrate
    $ python manage.py createsuperuser
    $ python manage.py runserver

Then:

1. Visit http://localhost:8000/admin. Login with your superuser account
2. Create a DDSApplicationCredential with an agent key and DukeDS API root URL.
3. Create a DDSUserCredential object with a user key as the token
4. Visit http://localhost:8000/data/ and navigate projects
