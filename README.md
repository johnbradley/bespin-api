# bespin-api

Web application for running workflows in the cloud.

## Development Usage
This application uses postgres-specific features, so you'll need a postgres server.

```
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py runserver
```


# Docker Build Details

The [Dockerfile](Dockerfile) in the repo root builds `bespin-api` in a development configuration (running django's web server).

    docker build -t bespin-api .

To build a production-ready image (Apache with mod\_wsgi), use the [Dockerfile](apache-docker/Dockerfile) in the apache-docker subdirectory, specifying the prior image name as the BASE\_IMAGE argument:

    docker build --build-arg BASE_IMAGE=bespin-api -t bespin-api:apache apache-docker

See [apache-docker](apache-docker) for more details on running the production-ready image.
