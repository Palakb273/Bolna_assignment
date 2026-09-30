"""Write/check a synthetic restart marker using the restricted application role."""
import json
import sys
from pathlib import Path
from uuid import uuid4, UUID
from app.database import make_engine
from app.repository import Repository
from app.domain.address import AddressChanges
from app.domain.session import update_candidate

values = dict(line.split('=',1) for line in Path('local-data/development.env').read_text().splitlines() if '=' in line)
repo = Repository(make_engine(values['DATABASE_URL']))
path = Path('local-data/restart-marker.json')
if sys.argv[1] == 'write':
    s, token = repo.create('durability-'+str(uuid4()), 'durability-'+str(uuid4()))
    repo.mutate(s.session_id,token,0,lambda s:update_candidate(s,0,AddressChanges(house_flat='Synthetic restart marker')))
    path.write_text(json.dumps({'session_id':str(s.session_id),'token':token}))
    print('Synthetic durability marker committed.')
else:
    marker = json.loads(path.read_text())
    s = repo.get(UUID(marker['session_id']),marker['token'])
    assert s.current_version == 1 and s.versions[0].canonical.house_flat == 'Synthetic restart marker'
    print('PostgreSQL restart durability: PASS')
repo.engine.dispose()
