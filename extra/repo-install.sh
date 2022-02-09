#!/bin/bash
#
# A script for the lazy folk and probably a butchering of git.
# Run this script once you have **ALL OF THE DEPENDENCIES** set up and
# updated; this also include dependencies **OUTSIDE OF PYTHON**, like
# 'opusfile-devel' on Fedora.
# Either way, the debug message pointing out what is missing when
# compiling PHAzOR (line #34) helps you find out what is needed.
# Those packages usually have similar enough names to be found quite
# easily by your package manager of choice.
#
# The script below installs the TauonMusicBox repo as a desktop app by
# cloning files into temporary ones and changing+deploying them;
# lines #38 to #44. I did it because I was too lazy to learn RPM
# packaging :B
#
# If you're running it for the very first time
# (and just to be on the safe side), then the repository itself should
# probably be cleansed, as in:
#   ----------------------------------
#   git reset --hard && git clean -dfx
#   ----------------------------------
#
# NEVER run this script as sudo!
# Thank you.

RepoDir=$(realpath $(dirname "$0")/..)
ShareDir=~/.local/share
cd $RepoDir

set -e

rm -fR lib
sh compile-phazor.sh

python3 compile-translations.py

cp -f extra/tauonmb.{,tmp.}desktop

sed -i -e "s+/opt/tauon-music-box/tauonmb.sh %U+python3 $RepoDir/tauon.py+g" -e "s+/opt/tauon-music-box/tauonmb.sh --no-start +curl http://localhost:7813/+g" -e "s+--play-pause+playpause/+g" -e "s+--previous+previous/+g" -e "s+--next+next/+g" -e "s+--stop+stop/+g" extra/tauonmb.tmp.desktop

mkdir -p $ShareDir/{applications,icons/hicolor/scalable/apps}
install -Dm755 extra/tauonmb.tmp.desktop $ShareDir/applications/tauonmb.desktop
install -Dm644 extra/tauonmb{,-symbolic}.svg $ShareDir/icons/hicolor/scalable/apps/

rm -fR extra/tauonmb.tmp.desktop

# This lines uses sudo to update your desktop apps list so you can
# open it from the menu as soon as it is ready.
sudo update-desktop-database

echo -e "\n== == == == == ==\n\
 Setup finished!\n\
== == == == == =="
