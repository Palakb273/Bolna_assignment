"""Explicit unverified demo import; never labels a file official. No raw-row output."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from app.settings import Settings
from app.validation.demo_postal import import_demo_csv
from app.validation.postal_directory import PostalDataError


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reject-malformed-rows',action='store_true')
    args=parser.parse_args()
    cfg=Settings.from_env()
    if not cfg.allow_unverified_postal_data:
        parser.error('Explicit development/test unverified mode required.')
    try:
        artifact,report=import_demo_csv(args.input,reject_malformed_rows=args.reject_malformed_rows)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        temp_path=None
        try:
            with tempfile.NamedTemporaryFile(dir=args.output.parent,delete=False) as f:
                temp_path=Path(f.name)
                f.write(artifact.model_dump_json().encode('utf-8'))
                f.flush()
                os.fsync(f.fileno())
            os.link(temp_path,args.output)
        finally:
            if temp_path: temp_path.unlink(missing_ok=True)
        with args.output.with_suffix('.report.json').open('x',encoding='utf-8') as f:
            json.dump(report,f,indent=2)
        print(json.dumps(report))
    except (PostalDataError,OSError) as exc:
        parser.exit(1,(exc.code if isinstance(exc,PostalDataError) else 'POSTAL_OUTPUT_FAILED')+'\n')


if __name__=='__main__':
    main()
