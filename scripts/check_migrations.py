"""Round-trip migrations in a new disposable PostgreSQL database, never the app DB."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg import sql


def main():
    values = dict(line.split('=', 1) for line in Path('local-data/development.env').read_text().splitlines() if '=' in line)
    name = 'bolna_migration_test_'+uuid4().hex
    with psycopg.connect(host='127.0.0.1', port=55432, dbname='postgres', user='bolna_owner',
                         password=values['POSTGRES_PASSWORD'], autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = f"postgresql+psycopg://bolna_owner:{values['POSTGRES_PASSWORD']}@127.0.0.1:55432/{name}"
            for args in [('upgrade','head'),('downgrade','base'),('upgrade','head')]:
                result = subprocess.run([sys.executable,'-m','alembic',*args], env=env, capture_output=True)
                if result.returncode:
                    raise RuntimeError('Migration round-trip failed; output withheld to avoid connection-detail exposure.')
            print('Real PostgreSQL migration upgrade/downgrade/upgrade: PASS')
        finally:
            conn.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))


if __name__ == '__main__':
    main()
