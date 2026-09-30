"""Run local commands with generated credentials without exposing them in output."""
import os
import subprocess
import sys
from pathlib import Path


def main():
    mode = sys.argv[1]
    values = dict(line.split('=', 1) for line in Path('local-data/development.env').read_text().splitlines() if '=' in line)
    env = os.environ.copy()
    env.update(values)
    if mode == 'migrate':
        env['DATABASE_URL'] = f"postgresql+psycopg://bolna_owner:{values['POSTGRES_PASSWORD']}@127.0.0.1:55432/bolna"
        command = [sys.executable, '-m', 'alembic', *sys.argv[2:]]
    elif mode == 'test':
        env['TEST_DATABASE_URL'] = values['DATABASE_URL']
        command = [sys.executable, '-m', 'pytest', *sys.argv[2:]]
    elif mode == 'serve':
        command = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log']
    else:
        raise SystemExit('Use migrate, test or serve.')
    raise SystemExit(subprocess.call(command, env=env))


if __name__ == '__main__':
    main()
