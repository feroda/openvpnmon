#!/bin/bash

# Place this file in your OpenVPN home directory
# OpenVPN directive
# client-disconnect ./client-disconnected.sh

python /path/to/your/django-openvpnmon-installation/manage.py client_disconnect
