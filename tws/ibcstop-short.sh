#!/bin/bash

{ sleep 2; echo "STOP"; } | telnet 127.0.0.1 4005
exit 0

