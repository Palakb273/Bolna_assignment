"""Validate one test call by default; --execute submits it once."""

import argparse
import sys

from bolna_common import build_call_payload, post_json, required_env, response_identifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--to', required=True, help='Consenting test recipient in E.164 format.')
    parser.add_argument('--execute', action='store_true', help='Place one real call; charges may apply.')
    args = parser.parse_args(argv)
    try:
        payload = build_call_payload(required_env('BOLNA_AGENT_ID'), args.to)
        if not args.execute:
            print('Call inputs validated locally. No request sent.')
            return 0
        response = post_json('/call', payload, required_env('BOLNA_API_KEY'))
        print('Call submitted; execution ID: ' + response_identifier(response, 'execution_id'))
        return 0
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
