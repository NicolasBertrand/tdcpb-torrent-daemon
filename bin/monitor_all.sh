#!/bin/bash
COMMAND="/var/lib/tdcpb-torrents/tdcpb-torrent-daemon/venv/bin/python scripts/monitor_all.py"
DIRECTORY="/var/lib/tdcpb-torrents/tdcpb-torrent-daemon"

cd ${DIRECTORY}
$COMMAND

