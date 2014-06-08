#!/bin/sh
#
### BEGIN INIT INFO
# Provides:          jobqueuemanager
# Required-Start:    $local_fs $network $remote_fs
# Required-Stop:     $local_fs $network $remote_fs
# Should-Start:      $NetworkManager
# Should-Stop:       $NetworkManager
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of Job Queue Manager
# Description:       starts instance of Job Queue Manager using start-stop-daemon
### END INIT INFO

# Source JobQueueManager configuration
if [ -f /etc/default/jobqueuemanager ]; then
    . /etc/default/jobqueuemanager
else
    echo "/etc/default/jobqueuemanager not found using default settings.";
fi

# Script name
NAME=jobqueuemanager

# App name
DESC=JobQueueManager

## Don't edit this file
## Edit user configuation in /etc/default/jobqueuemanager to change
##
## JQM_USER=        #$RUN_AS, username to run JobQueueManager under, the default is jqm
## JQM_HOME=        #$APP_PATH, the location of jobqueue_daemon.py, the default is /opt/jqm
## JQM_DATA=        #$DATA_DIR, the location of jqm.db, cache, logs, the default is /opt/jqm
## JQM_PIDFILE=     #$PID_FILE, the location of jqm.pid, the default is /run/jqm.pid
## PYTHON_BIN=      #$DAEMON, the location of the python binary, the default is /usr/bin/python3
## JQM_OPTS=        #$EXTRA_DAEMON_OPTS, extra cli option for jobqueuemanager, i.e. " --config=${JQM_HOME}/config.ini"
## SSD_OPTS=        #$EXTRA_SSD_OPTS, extra start-stop-daemon option like " --group=users"
##
## EXAMPLE if want to run as different user
## add JQM_USER=username to /etc/default/jobqueuemananger
## otherwise default jqm is used

## The defaults
# Run as username
RUN_AS=${JQM_USER-jqm}

# Path to app JQM_HOME=path/to/app/jobqueue_daemon.py
APP_PATH=${JQM_HOME-/opt/jqm}

# Data directory where jqm.db, cache and logs are stored
DATA_DIR=${JQM_DATA-/opt/jqm}

# Path to store PID file
PID_FILE=${JQM_PIDFILE-/run/jqm.pid}

# path to python bin
DAEMON=${PYTHON_BIN-/usr/bin/python3}

# Extra daemon option like: JQM_OPTS=" --config=${JQM_HOME}/config.ini"
EXTRA_DAEMON_OPTS=${JQM_OPTS-}

# Extra start-stop-daemon option like START_OPTS=" --group=users"
EXTRA_SSD_OPTS=${SSD_OPTS-}
##

PID_PATH=`dirname $PID_FILE`
DAEMON_OPTS=" job-daemon.py -q --daemon --pidfile=${PID_FILE} --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}"
##

test -x $DAEMON || exit 0

set -e

# Create PID directory if not exist and ensure the JobQueueManager user can write to it
if [ ! -d $PID_PATH ]; then
    mkdir -p $PID_PATH
    chown $RUN_AS $PID_PATH
fi

if [ ! -d $DATA_DIR ]; then
    mkdir -p $DATA_DIR
    chown $RUN_AS $DATA_DIR
fi

if [ -e $PID_FILE ]; then
    PID=`cat $PID_FILE`
    if ! kill -0 $PID > /dev/null 2>&1; then
        echo "Removing stale $PID_FILE"
        rm $PID_FILE
    fi
fi

case "$1" in
    start)
        echo "Starting $DESC"
        start-stop-daemon -d $APP_PATH -c $RUN_AS $EXTRA_SSD_OPTS --start --pidfile $PID_FILE --exec $DAEMON -- $DAEMON_OPTS
        ;;

    stop)
        echo "Stopping $DESC"
        start-stop-daemon --stop --pidfile $PID_FILE --retry 15
        ;;

    restart|force-reload)
        echo "Restarting $DESC"
        start-stop-daemon --stop --pidfile $PID_FILE --retry 15
        start-stop-daemon -d $APP_PATH -c $RUN_AS $EXTRA_SSD_OPTS --start --pidfile $PID_FILE --exec $DAEMON -- $DAEMON_OPTS
        ;;

    status)
        # Use LSB function library if it exists
        if [ -f /lib/lsb/init-functions ]; then
            . /lib/lsb/init-functions

            if [ -e $PID_FILE ]; then
                status_of_proc -p $PID_FILE "$DAEMON" "$NAME" && exit 0 || exit $?
            else
                log_daemon_msg "$NAME is not running"
                exit 3
            fi

        else
        # Use basic functions
            if [ -e $PID_FILE ]; then
                PID=`cat $PID_FILE`
                if kill -0 $PID > /dev/null 2>&1; then
                    echo " * $NAME is running"
                    exit 0
                fi
            else
                echo " * $NAME is not running"
                exit 3
            fi
        fi
        ;;

    *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|force-reload|status}" >&2
        exit 1
        ;;
esac

exit 0
