"""Bind projections to immutable versions and enforce non-null validation on consent."""
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint('confirmed_requires_validation', 'address_sessions',
        'confirmed_version IS NULL OR (validated_version IS NOT NULL AND confirmed_version = validated_version)')
    for table, session_col, version_col in [('validation_attempts','session_id','address_version'),
        ('readback_attempts','session_id','address_version'), ('confirmation_events','session_id','address_version'),
        ('addresses','source_session_id','source_version')]:
        op.create_foreign_key(table+'_version_fk', table, 'address_versions',
            [session_col, version_col], ['session_id','version'])
    op.create_foreign_key('readback_validation_fk','readback_attempts','validation_attempts', ['validation_attempt_id'],['attempt_id'])
    op.create_foreign_key('confirmation_readback_fk','confirmation_events','readback_attempts',['readback_attempt_id'],['attempt_id'])


def downgrade():
    op.drop_constraint('confirmation_readback_fk','confirmation_events',type_='foreignkey')
    op.drop_constraint('readback_validation_fk','readback_attempts',type_='foreignkey')
    for table in ['validation_attempts','readback_attempts','confirmation_events','addresses']:
        op.drop_constraint(table+'_version_fk',table,type_='foreignkey')
    op.drop_constraint('confirmed_requires_validation','address_sessions',type_='check')
