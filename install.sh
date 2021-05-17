# In progress!..

if [[ $(id -u) != "0" ]]; then
    echo "Script needs to run under the root!"
    exit 1
fi

echo

if [ -e /opt/tauon-music-box/tauon.py ] || [ -e /usr/li*/tauon-music-box/tauon.py ]; then

    echo "Uhm.. Tauon already installed I guess."
    read -r -p "Wanna uninstall?[Y/n]: " VER
    case $VER in
    [yY][eE][sS]|[yY]|"")
        echo
        (
        cd /opt/tauon-music-box
        pip3 uninstall -r requirements.txt
        )
        rm -rf /usr/share/applications/tauonmb.desktop
        rm -rf /usr/bin/tauon*
        rm -rf /bin/tauon*
        rm -rf /usr/li*/tauon-music-box
        rm -rf /opt/tauon-music-box
        read -r -p "Do you want install Tauon?[Y/n]: " VER
        while true; do
            case $VER in
            [yY][eE][sS]|[yY]|"")
                echo
            break;;
            [nN][oO]|[nN])
                echo
                exit 0
            ;;
            *)
                echo
                read -r -p "Please.. Is this Yes/no?: " VER
            ;;
            esac
        done
    ;;
    [nN][oO]|[nN])
        echo
        echo "Aborted."
        exit 0
    ;;
    *)
        echo
        echo "I'm.. not sure how to respond"
        echo "Run again."
        exit 1
    ;;
    esac
    
fi

# case statement for several distributions

read -r -p "Is your distribution based on Debian/Ubuntu?[y/n]: " VER
while true; do
    case $VER in
    [yY][eE][sS]|[yY])
        echo
        echo "Sorry, Installer is under maintain at moment for Debian/Ubuntu based distributions."
        exit 1
        #apt update
        #apt install -y python3-pip
    break;;
    [nN][oO]|[nN])
        echo
    break;;
    *)
    echo
    read -r -p "Please.. Is this yes/no?: " VER
    ;;
    esac
done

read -r -p "Is your distribution based on Fedora?[y/n]: " VER
while true; do
    case $VER in
    [yY][eE][sS]|[yY])
        echo
        dnf update
        dnf install -y python3-pip SDL2-image libopenmpt
        #PHAZOR dependencies, don't forget
    break;;
    [nN][oO]|[nN])
        echo
    break;;
    *)
    echo
    read -r -p "Please.. Is this yes/no?: " VER
    ;;
    esac
done

#
# Missing libopenmpt,*flac*, *opus* on debian
# Missing unknown ddt dependency on debian
#

echo

pip3 install -r requirements.txt
#pip3 install ddt
echo

(
cd ..

if [ -e TauonMusicBox-*/tauon.py ]; then
    cp -r TauonMusicBox-* /opt/tauon-music-box
else
    echo "TauonMusicBox not found. (Perhaps you're running from cloned directory?)"
    echo
    echo "Please download latest official release from https://github.com/Taiko2k/TauonMusicBox/releases/"
    echo "extract the file and run again."
    exit 1
fi


(
cd /opt/tauon-music-box/
rm -rf TauonMusicBox-*
cp extra/tauonmb.sh tauonmb.sh
chmod +x tauonmb.sh
#chmod +x compile-phazor.sh
#./compile-phazor.sh
)

(
cd /usr/bin
ln -s /opt/tauon-music-box/tauonmb.sh ./tauonmb
)

mkdir -p /usr/share/applications
cp /opt/tauon-music-box/extra/tauonmb.desktop /usr/share/applications/tauonmb.desktop

echo

read -r -p "Remove the source file?[Y/n]: " VER

case $VER in
   [yY][eE][sS]|[yY]|"")
echo
rm -rf TauonMusicBox-*
;;
   [nN][oO]|[nN])
echo
echo "Ok, I left the folder."
      ;;
   *)
echo
echo "I'm.. not sure how to respond?"
echo "I left it."
;;
esac
)

echo

echo
echo "Done"
echo "Installation completed."
