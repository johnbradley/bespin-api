#!/usr/bin/env bash

# ensure database is migrated before each start of the production application
python manage.py migrate

# Apache gets grumpy about PID files pre-existing
rm -f /var/run/apache2/apache2.pid

apachectl -DFOREGROUND
