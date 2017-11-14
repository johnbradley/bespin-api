bespin-api: apache-docker
=====================

Dockerfile for building bespin-api with apache2 and mod_wsgi

# Usage

The Dockerfile contained is used to build an image containing the bespin-api Django application, hosted by Apache httpd using wsgi.

The Ember frontend application, [bespin-ui](https://github.com/Duke-GCB/bespin-ui) is not included in the image, but should be downloaded from its release and mounted at runtime in the container at `/srv/ui/`.

# Docker Build Details

The [Dockerfile](Dockerfile) requires a build-time argument to specify the `FROM` image. Specifying the `FROM` image allows Docker Cloud to automatically build an `-apache` variation for each tagged version of the `bespin-api` image.

Docker cloud is configured to build `bespin-api` tags and branches. The [post-build hook](../hooks/post_build) builds the `-apache` variation and the [post-push hook](../hooks/post_push) pushes the apache variation.


    docker build \
      --build-arg BASE_IMAGE=dukegcb/bespin-api:1.0.0 \
      -t dukegcb/bespin-api:1.0.0-apache
      .

