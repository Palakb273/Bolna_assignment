"""Run after editable package installation. No credentials or customer data needed."""
import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from app.validation.postal_directory import ImportMetadata, PostalDataError, import_csv


def main():
    parser = argparse.ArgumentParser(description='Import an operator-verified official postal CSV.')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resource-url', required=True)
    parser.add_argument('--resource-id', required=True)
    parser.add_argument('--source-date', type=date.fromisoformat, required=True)
    parser.add_argument('--retrieved-at', type=datetime.fromisoformat)
    parser.add_argument('--source-kind', choices=['OFFICIAL_POSTAL_DIRECTORY', 'UNVERIFIED_OR_STALE'], default='UNVERIFIED_OR_STALE')
    args = parser.parse_args()
    try:
        result = import_csv(args.input, args.output, ImportMetadata(source_name='Department of Posts',
            resource_url=args.resource_url, resource_id=args.resource_id, source_date=args.source_date,
            imported_at=datetime.now(timezone.utc), retrieved_at=args.retrieved_at, source_kind=args.source_kind))
    except PostalDataError as exc:
        parser.exit(1, exc.code + '\n')
    print(result.model_dump_json(indent=2))


if __name__ == '__main__':
    main()
