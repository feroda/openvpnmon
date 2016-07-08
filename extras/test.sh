#!/bin/bash

# Execute this script as your openvpn user

if [ -z "$1" ]; then
    echo "Usage $0 <client_connect|client_disconnect>"
    exit 1
fi

export common_name="prova-cn"
export trusted_ip="1.2.3.4"
export ifconfig_remote="123.123.123.123"
export ifconfig_pool_remote_ip="123.124.125.126"
export dev="tun0"
export time_unix=1295718141
export time_duration=12957
export bytes_sent=1295718141
export bytes_received=1295718141


python /usr/local/openvpnmon/manage.py $1
