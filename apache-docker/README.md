bespin-api: apache-docker
=====================

Dockerfile for building bespin-api with apache2 and mod_wsgi

# Usage

The Dockerfile contained is used to build an image containing the bespin-api Django application, hosted by Apache httpd using wsgi.

The Ember frontend application, [bespin-ui](https://github.com/Duke-GCB/bespin-ui) is not included in the image, but should be built for production and mounted at runtime in the container at `/srv/ui/`.

 The [bespin\_web](https://github.com/Duke-GCB/gcb-ansible-roles/blob/master/bespin_web/tasks/run-server.yml) ansible role illustrates how the built Ember application can be served from a Docker volume.

# Docker Build Details

The [Dockerfile](Dockerfile) requires a build-time argument to specify the `FROM` image. This may be automated as in the [build\_docker\_image](https://github.com/Duke-GCB/gcb-ansible-roles/blob/master/build_docker_image/tasks/main.yml) ansible role, or built with the [docker command](https://docs.docker.com/engine/reference/commandline/build/)
