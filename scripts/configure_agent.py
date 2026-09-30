"""Validate locally by default; --execute creates one new hosted agent."""

import argparse
import sys

from bolna_common import load_agent_payload, post_json, required_env, response_identifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Create a new agent in Bolna (does not place a call).')
    args = parser.parse_args(argv)
    try:
        payload = load_agent_payload()
        if not args.execute:
            print('Configuration validated locally. No request sent; provider availability is unverified.')
            return 0
        response = post_json('/v2/agent', payload, required_env('BOLNA_API_KEY'))
        print('Agent created: ' + response_identifier(response, 'agent_id'))
        return 0
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
