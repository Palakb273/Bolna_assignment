"""User-authorized loading of only two Bolna keys; never prints file contents."""
import os
from pathlib import Path


def load_bolna_keys():
    allowed = {'BOLNA_API_KEY', 'BOLNA_AGENT_ID'}
    for line in Path('.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        if key in allowed and not os.getenv(key):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ[key] = value
