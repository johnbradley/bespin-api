# bespin-api

Web application for running workflows in the cloud

## Development Usage

```
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py runserver
```


# Docker Build Details

Docker Cloud is configured to automatically build the master branch and tags of `bespin-api`, producing docker images that run bespin-api in development mode:

```
master -> dukegcb/bespin-api:latest
v1.0.0 -> dukegcb/bespin-api:1.0.0
```

For automated builds of production-ready images, there is a second [Dockerfile](apache-docker/Dockerfile) in   [apache-docker](apache-docker). We use Docker Cloud's [custom build phase hooks](https://docs.docker.com/docker-cloud/builds/advanced/#custom-build-phase-hooks) in the [hooks](hooks) directory build and push `-apache` variations of the bespin-api images.

The [post\_build](hooks/post_build) and [post\_push](../hooks/post_push) hooks produce docker images that run bespin-api in production mode:

```
master -> dukegcb/bespin-api:latest-apache
v1.0.0 -> dukegcb/bespin-api:1.0.0-apache
```

See [apache-docker](apache-docker) for more details, including
