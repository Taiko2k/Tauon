#!/bin/bash
#
# Removes everything 'extra/repo-install.sh' creates.

RepoDir=$(realpath $(dirname "$0")/..)
cd $RepoDir

rm -f extra/tauonmb.tmp.* ~/.local/share/{applications/tauonmb.desktop,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
sudo update-desktop-database
