#!/bin/bash
#
# Removes everything 'extra/repo-install.sh' creates.

RepoDir=$(realpath $(dirname "$0")/..)
ShareDir=~/.local/share
cd $RepoDir

set -e

rm -f $ShareDir/{applications/tauonmb.desktop,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
sudo update-desktop-database

echo -e "\n== == == == == == ==\n\
 Uninstall finished.\n\
== == == == == == =="
