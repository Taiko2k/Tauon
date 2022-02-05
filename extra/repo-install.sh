#!/bin/bash
#
# A script for the lazy folk and probably a butchering of git.
# Run this script once you have ALL the dependencies set up and updated; this also include dependencies outside of Python, like 'opusfile-devel' on Fedora. Either way, the debug message pointing out what is missing when compiling PHAzOR (line #16) helps you find out what is needed. Usually those packages have similar enough names to be found quite easily by your package manager of choice.
# The script below installs the TauonMusicBox repo as a desktop app by cloning files into temporary ones and changing+deploying them; lines #18 to #23. I did it because I was too lazy to learn RPM packaging :B
# If you're running it for the very first time (and just to be on the safe side), then the repository itself should probably be cleansed, as in:
#   ----------------------------------
#   git reset --hard && git clean -dfx
#   ----------------------------------
# Thank you.

RepoDir=$(realpath $(dirname "$0")/..)
cd $RepoDir

rm -f lib/*
sh compile-phazor.sh || exit 0

cp -f extra/tauonmb.{,tmp.}desktop
cp -f extra/tauonmb.{,tmp.}sh

sed -i "s+/opt/tauon-music-box/tauonmb+sh $RepoDir/extra/tauonmb.tmp+g" extra/tauonmb.tmp.desktop
sed -i '1a cd $(realpath $(dirname "$0")/..)' extra/tauonmb.tmp.sh
sed -i "s+/opt/tauon-music-box+$RepoDir+g" extra/tauonmb.tmp.sh

install -Dm755 extra/tauonmb.tmp.desktop ~/.local/share/applications/tauonmb.desktop
install -Dm644 extra/tauonmb{,-symbolic}.svg ~/.local/share/icons/hicolor/scalable/apps/

# This lines uses sudo to update your desktop apps list so you can open it from the menu as soon as it is ready.
# NEVER run the script itself as sudo, though.
sudo update-desktop-database
