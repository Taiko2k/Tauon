
import subprocess
import os

if not os.path.isfile("pygettext.py"):
    print("ERROR: Please add a copy of pygettext.py to this dir from the Python Tools dir")
    exit()

locale_folder = "locale"
pot_path = os.path.join(locale_folder, "messages.pot")

print("Generate template")
subprocess.run(['python', "pygettext.py", "t_modules/t_dbus.py", "t_modules/t_extra.py", "t_modules/t_jellyfin.py", "t_modules/t_main.py", "t_modules/t_phazor.py", "t_modules/t_spot.py", "t_modules/t_stream.py", "t_modules/t_tidal.py", "t_modules/t_webserve.py"])
print("Copy template")
subprocess.run(['cp', "messages.pot", pot_path])
subprocess.run(['rm', "messages.pot"])

lang = os.listdir(locale_folder)

for l in lang:

    if l == "messages.pot":
        continue

    po_path = os.path.join(locale_folder, l, "LC_MESSAGES", "tauon.po")
    
    if os.path.exists(po_path):
        subprocess.run(['msgmerge', '-U', po_path, pot_path])

        print(f"Updated: {l}")

    else:
        print(f"Missing po file: {po_path}")

print("Done")


