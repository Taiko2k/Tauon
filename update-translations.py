
import subprocess
import os

locale_folder = "locale"
pot_path = os.path.join(locale_folder, "messages.pot")

print("Generate template")
subprocess.run(['python', "pygettext.py", "tauon.py", "--no-location"])
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

