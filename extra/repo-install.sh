#!/bin/bash
#
# A script for the lazy folk and probably a butchering of git.
#
# Run this script once you have ALL the dependencies set up.
#
# If you're running it for the 1st time (and in order to appease my OCD), the repository itself should
# probably be clean, as in:
# -------------------------------------------------------------------------------------------------------
#   git reset --hard && git clean -dfx
# -------------------------------------------------------------------------------------------------------
#
# It wonkly deploys the TauonMusicBox repo as a desktop app by modifying the existing files. By doing so
# we use the app directly from the repo... I did it because I was too lazy to learn RPM packaging :B
#
# This and 'repo-uninstall-as-is.sh' are best used on a repo with --depth=1; one you will NOT work on.
#
# Thank you.

RepoDir=$(realpath $(dirname "$0")/..)
cd $RepoDir

rm -f lib/*
sh compile-phazor.sh || exit 0
sed -i "s+/opt/tauon-music-box+sh $RepoDir/extra+g" extra/tauonmb.desktop
sed -i '1a cd $(realpath $(dirname "$0")/..)' extra/tauonmb.sh
sed -i "s+/opt/tauon-music-box+$RepoDir+g" extra/tauonmb.sh

install -Dm755 extra/tauonmb.desktop ~/.local/share/applications/tauonmb.desktop
install -Dm644 extra/tauonmb-symbolic.svg ~/.local/share/icons/hicolor/scalable/apps/tauonmb-symbolic.svg
install -Dm644 extra/tauonmb.svg ~/.local/share/icons/hicolor/scalable/apps/tauonmb.svg

# This lines uses sudo to update your desktop apps list so you can open it from the menu as soon as it is
# ready.
# I recommend never running the script itself as sudo, though.
sudo update-desktop-database
