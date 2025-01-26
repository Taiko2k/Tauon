---
name: Bug report
about: Create a report to help us improve
title: ''
labels: unconfirmed bug
assignees: ''

---

**Desktop (please complete the following information):**
 - OS: [e.g. Arch Linux/Windows/macOS]
 - Tauon Version [e.g. 7.9.0, see Menu->Settings->About]

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Tauon log**

<details><summary>Logfiles</summary>

Python stack trace log example:

```python
Traceback (most recent call last):
  File "/app/bin/tauon.py", line 359, in <module>
    exec(main)
  File "/app/bin/t_modules/t_main.py", line 4333, in <module>
    auto_scale()
  File "/app/bin/t_modules/t_main.py", line 4302, in auto_scale
    prefs.scale_want = window_size[0] / logical_size[0]
                       ~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~
ZeroDivisionError: division by zero
```

Tauon log example (or attach as file):
```log
17:52:16 [DEBUG] Starting new HTTPS connection (1): api.listenbrainz.org:443
17:52:16 [DEBUG] https://api.listenbrainz.org:443 "POST /1/submit-listens HTTP/1.1" 200 16
17:52:22 [ INFO  ] Open - requested start was 0 (0)
17:52:22 [ INFO  ] Extension: mp3
17:52:22 [ INFO  ] After Dark -> After Dark
17:52:22 [ INFO  ]  --- length: 259.146
17:52:22 [ INFO  ]  --- position: 257.106
17:52:22 [ INFO  ]  --- We are 2.0400000000000205 from end
17:52:22 [ INFO  ] Transition gapless
17:52:22 [ INFO  ] Submit Scrobble Mr.Kitty - After Dark
17:52:22 [DEBUG] Starting new HTTPS connection (1): api.listenbrainz.org:443
17:52:22 [DEBUG] https://api.listenbrainz.org:443 "POST /1/submit-listens HTTP/1.1" 200 16
17:52:36 [ INFO  ] Auto save playtime
```

</details>

**Additional context**
Add any other context about the problem here.
