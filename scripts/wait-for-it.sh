#!/bin/bash
# wait-for-it.sh script from https://github.com/vishnubob/wait-for-it

WAITFORIT_cmdname=${0##*/}

echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $WAITFORIT_cmdname host:port [-s] [-t timeout] [-- command args]
    -h HOST | --host=HOST       Host or IP under test
    -p PORT | --port=PORT       TCP port under test
    -s | --strict               Only execute subcommand if the test succeeds
    -q | --quiet                Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    for i in `seq $WAITFORIT_TIMEOUT` ; do
        nc -z "$WAITFORIT_HOST" "$WAITFORIT_PORT" > /dev/null 2>&1
        
        result=$?
        if [ $result -eq 0 ] ; then
            if [ $# -gt 0 ] ; then
                exec "$@"
            fi
            exit 0
        fi
        sleep 1
    done
    echo "Operation timed out" >&2
    exit 1
}

WAITFORIT_HOST=127.0.0.1
WAITFORIT_PORT=80
WAITFORIT_TIMEOUT=15
WAITFORIT_QUIET=0
WAITFORIT_STRICT=0
WAITFORIT_CHILD=0
WAITFORIT_ARGS=()

while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        WAITFORIT_HOST="${1%:*}"
        WAITFORIT_PORT="${1#*:}"
        shift 1
        ;;
        -q | --quiet)
        WAITFORIT_QUIET=1
        shift 1
        ;;
        -s | --strict)
        WAITFORIT_STRICT=1
        shift 1
        ;;
        -t)
        WAITFORIT_TIMEOUT="$2"
        if [[ $WAITFORIT_TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        WAITFORIT_TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        WAITFORIT_ARGS+=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$WAITFORIT_HOST" == "" || "$WAITFORIT_PORT" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

wait_for "${WAITFORIT_ARGS[@]}" 