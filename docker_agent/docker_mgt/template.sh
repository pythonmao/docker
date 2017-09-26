#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Error, this script need two args"
    exit 1
fi

log_file=$1
touch $log_file
chmod -R 777 $log_file
$2 > $log_file
