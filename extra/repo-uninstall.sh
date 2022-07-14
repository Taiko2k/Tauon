#!/bin/bash
#
# Removes everything 'extra/repo-install.sh' creates.

ShareDir=~/.local/share

set -e

rm -f $ShareDir/{applications/tauonmb.desktop,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
sudo update-desktop-database

echo -e "\n== == == == == == ==\n\
 Uninstall finished.\n\
== == == == == == =="
