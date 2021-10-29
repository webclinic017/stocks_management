#!/bin/bash

NAME="kadima_project"                                   # Name of the application
DJANGODIR=/home/ubuntu/stocks_management               # Django project directory
SOCKFILE=/home/ubuntu/stocks_management/venv_kadima/run/gunicorn.sock  # we will communicte using this unix socket
USER=ubuntu                                         # the user to run as
GROUP=ubuntu                                        # the group to run as
NUM_WORKERS=3                                      # how many worker processes should Gunicorn spawn
WORKER_CLASS=gevent
WORKER_CONNECTIONS=1000
THREADS=8
TIMEOUT=400
DJANGO_SETTINGS_MODULE=kadima_project.settings      # which settings file should Django use
DJANGO_WSGI_MODULE=kadima_project.wsgi              # WSGI module name
echo "Starting $NAME as `whoami`"

# Activate the virtual environment

cd $DJANGODIR
source /home/ubuntu/stocks_management/venv_kadima/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)

exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --threads $THREADS \
  --worker-connections $WORKER_CONNECTIONS \
  --user=$USER --group=$GROUP \
  --timeout $TIMEOUT \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-