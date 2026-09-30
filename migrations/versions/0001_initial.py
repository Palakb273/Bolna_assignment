"""Initial schema. Schema snapshot lives in migrations/schema_v1.py."""
from alembic import op
from migrations.schema_v1 import metadata

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    metadata.create_all(op.get_bind())
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bolna_app') THEN GRANT USAGE ON SCHEMA public TO bolna_app; GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO bolna_app; END IF; END $$")
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bolna_app') THEN REVOKE UPDATE ON address_versions, validation_attempts, confirmation_events, audit_events, call_events FROM bolna_app; END IF; END $$")


def downgrade():
    metadata.drop_all(op.get_bind())
