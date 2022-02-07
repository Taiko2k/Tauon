#!/bin/bash
#
# Removes everything 'extra/repo-install.sh' creates.

RepoDir=$(realpath $(dirname "$0")/..)
ShareDir=~/.local/share
cd $RepoDir

set -e

rm -fR extra/tauonmb.tmp.* $ShareDir/{applications/tauonmb.desktop,locale,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
sudo update-desktop-database

echo -e "\n== == == == == == ==\n\
 Uninstall finished.\n\
== == == == == == =="
