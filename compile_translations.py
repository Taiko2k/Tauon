
import subprocess
import os

locale_folder = "locale"
lang = os.listdir(locale_folder)

for l in lang:

    if l == "messages.pot":
        continue

    po_path = os.path.join(locale_folder, l, "LC_MESSAGES", "tauon.po")
    mo_path = os.path.join(locale_folder, l, "LC_MESSAGES", "tauon.mo")

    if os.path.exists(po_path):
        subprocess.run(['msgfmt', '-o', mo_path, po_path])
        print(f"Compiled: {l}")

    else:
        print(f"Missing po file: {po_path}")

print("Done")
