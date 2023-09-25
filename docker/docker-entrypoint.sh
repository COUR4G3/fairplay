#!/bin/bash

set -e

export FAIRPLAY_BIND=${FAIRPLAY_BIND:='0.0.0.0:5000'}

if [ -v FAIRPLAY_BIND ]; then
    RUN_ARGS+=("-b")
    RUN_ARGS+=("${FAIRPLAY_BIND}")
fi

case "$1" in
    dev)
        shift
        host=${FAIRPLAY_BIND%%:*}
        port=${FAIRPLAY_BIND##*:}
        exec python -m fairplay run --debugger --reload -h $host -p $port "$@"
        ;;
    run)
        shift
        exec gunicorn "$@" "${RUN_ARGS[@]}" "fairplay:create_app()"
        ;;
    *)
        exec python -m fairplay "$@"
        exit $?
esac

exit 1
