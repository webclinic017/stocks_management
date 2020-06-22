#!/bin/bash
# ibcstop.sh exit with code 0 on success, or code 1 otherwise
# Usage example:
#    ./ibcstop.sh 7462
# IP and PORT that IBC listens on for commands such as "STOP"

PORT=$1

# Note: by default IBC bind to public i-face, not 127.0.0.1
IP=127.0.0.1

# Number of attempts to try
ATTEMPTS=3

# Timeout (in seconds) to wait for IBC response
TIMEOUT_S=10

EXPECTED_REPLY="OK Shutting down"

# ------- do not edit after this line ---------------------------
if [ "$PORT" == "" ]; then
    echo "error: please specify the port to communicate with IBC (default 7462)." >&2
    exit 1
fi

for itry in `seq 1 ${ATTEMPTS}`; do
    # send STOP command
    OUTPUT=`{ sleep 5; echo "STOP"; } | nc -w ${TIMEOUT_S} ${IP} ${PORT}`
    echo "debug: OUTPUT: ${OUTPUT}"

    # You can even do case-insensitive substring matching natively in bash
    # using the regex operator =~ if you set the nocasematch shell option.
    # shopt -s nocasematch
    # check if got expected output

    if [[ "${OUTPUT}" =~ "${EXPECTED_REPLY}" ]]; then
        echo ${OUTPUT}
        # exit with success code (zero)
        exit 0
    fi
done

echo "error: failed to shut down after ${ATTEMPTS} attempt(s)"
exit 1