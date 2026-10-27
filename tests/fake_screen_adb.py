#!/usr/bin/env python3
"""A TV showing one app screen, for tests/test_appui.py.

TAB moves focus round VIEWS in order, OK ticks or unticks the focused checkbox, and taps are
ignored the way a phone-sized app window on a TV ignores them. `dumpsys backup` answers
BACKUP_FIRST_LINE."""
import json
import os
import sys
from pathlib import Path

d = Path(os.environ['FAKE_DIR'])
state_file = d / 'state.json'
views = os.environ.get('VIEWS', '').split()
state = json.loads(state_file.read_text()) if state_file.exists() else {'focus': 0, 'checked': []}
cmd = ' '.join(sys.argv[4:])
with (d / 'log').open('a') as f:
    f.write(cmd + '\n')

if cmd == 'dumpsys backup':
    print(os.environ['BACKUP_FIRST_LINE'])
    print('Last backup pass started: 0')
elif cmd.startswith('uiautomator dump'):
    print('<?xml version="1.0"?><hierarchy rotation="0">', end='')
    for i, v in enumerate(views):
        print(f'<node index="{i}" text="" resource-id="app:id/{v}" '
              f'checked="{str(v in state["checked"]).lower()}" '
              f'focused="{str(i == state["focus"]).lower()}" bounds="[0,0][10,10]" />', end='')
    print('</hierarchy>')
elif cmd == 'input keyevent KEYCODE_TAB':
    state['focus'] = (state['focus'] + 1) % len(views)
elif cmd == 'input keyevent KEYCODE_DPAD_CENTER':
    v = views[state['focus']]
    state['checked'] = [c for c in state['checked'] if c != v] if v in state['checked'] else state['checked'] + [v]
state_file.write_text(json.dumps(state))
