#!/bin/bash
#
# Uninstalls the app-repo, keeping the user-data and becoming just the good ol' repo

RepoDir=$(realpath $(dirname "$0")/..)
cd $RepoDir

git reset --hard

rm -f ~/.local/share/{applications/tauonmb.desktop,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
