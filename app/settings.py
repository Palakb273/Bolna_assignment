import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default='', repr=False)
    admin_token: str = field(default='', repr=False)
    webhook_token: str = field(default='', repr=False)
    evidence_token: str = field(default='', repr=False)
    postal_data_path: str = ''
    max_postal_source_age_days: int = 90
    app_env: str = 'production'
    allow_unverified_postal_data: bool = False
    demo_reject_malformed_rows: bool = False

    def __post_init__(self):
        if self.app_env not in {'production','development','test'}:
            raise ValueError('Unknown APP_ENV')
        if self.allow_unverified_postal_data and self.app_env not in {'development','test'}:
            raise ValueError('Unverified postal data is forbidden in production')
        if self.demo_reject_malformed_rows and not self.allow_unverified_postal_data:
            raise ValueError('Demo row exclusion requires explicit unverified mode')

    @classmethod
    def from_env(cls):
        def boolean(name):
            value=os.getenv(name,'false').lower()
            if value not in {'true','false'}:
                raise ValueError('Invalid boolean configuration: '+name)
            return value=='true'
        return cls(database_url=os.getenv('DATABASE_URL', ''), admin_token=os.getenv('BOLNA_SERVICE_TOKEN', ''),
            webhook_token=os.getenv('BOLNA_WEBHOOK_TOKEN', ''), evidence_token=os.getenv('EVIDENCE_ADAPTER_TOKEN', ''),
            postal_data_path=os.getenv('POSTAL_DATA_PATH', ''),
            max_postal_source_age_days=int(os.getenv('MAX_POSTAL_SOURCE_AGE_DAYS', '90')),
            app_env=os.getenv('APP_ENV', 'production'),
            allow_unverified_postal_data=boolean('ALLOW_UNVERIFIED_POSTAL_DATA'),
            demo_reject_malformed_rows=boolean('DEMO_REJECT_MALFORMED_ROWS'))
