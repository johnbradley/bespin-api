#!/bin/bash

# From https://docs.docker.com/compose/startup-order/

set -e

# Set environment variables for psql to read
export PGDATABASE=$POSTGRES_DB
export PGPASSWORD=$POSTGRES_PASSWORD
export PGUSER=$POSTGRES_USER
export PGHOST=$BESPIN_DB_HOST
cmd="$@"

until psql -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# Now set environment variables for django to read
export BESPIN_DB_NAME=$POSTGRES_DB
export BESPIN_DB_USER=$POSTGRES_USER
export BESPIN_DB_PASSWORD=$POSTGRES_PASSWORD

exec $cmd
