"""Generate separate ignored local credentials; never read or overwrite .env."""
from pathlib import Path
import secrets


def main():
    target = Path('local-data/development.env')
    target.parent.mkdir(exist_ok=True)
    values = {key: secrets.token_hex(24) for key in ('POSTGRES_PASSWORD', 'APP_DB_PASSWORD',
        'BOLNA_SERVICE_TOKEN', 'BOLNA_WEBHOOK_TOKEN', 'EVIDENCE_ADAPTER_TOKEN')}
    values['DATABASE_URL'] = f"postgresql+psycopg://bolna_app:{values['APP_DB_PASSWORD']}@127.0.0.1:55432/bolna"
    with target.open('x', encoding='utf-8') as handle:
        handle.write('\n'.join(f'{k}={v}' for k, v in values.items())+'\n')
    print('Created ignored local development configuration. No existing .env was accessed.')


if __name__ == '__main__':
    main()
