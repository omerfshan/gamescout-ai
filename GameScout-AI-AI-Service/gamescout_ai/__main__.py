"""Local Discovery & Autonomous Market Opportunity Scout CLI."""
import argparse
import json
import sys
from gamescout_ai.application.discovery import discover
from gamescout_ai.application.scout import VALID_PROVIDERS, run_market_scout
from gamescout_ai.domain.models import Scope, ValidationError
from gamescout_ai.infrastructure.json_source import load_file


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValidationError('INVALID_ARGUMENT', message)


def main(argv: list[str] | None = None) -> int:
    try:
        parser = Parser(description='GameScout AI — Discovery & Market Opportunity Scout CLI')
        sub = parser.add_subparsers(dest='command', required=True, parser_class=Parser)

        cli = sub.add_parser('discover')
        cli.add_argument('file')
        cli.add_argument('--platform', required=True, choices=('android', 'ios'))
        cli.add_argument('--max-games', type=int, default=10)
        cli.add_argument('--genre')
        cli.add_argument('--developer-profile', choices=('indie', 'small_team', 'unknown'))

        scout_cli = sub.add_parser('scout')
        scout_cli.add_argument('--provider', default='auto', choices=VALID_PROVIDERS)
        scout_cli.add_argument('--genre', default='all')
        scout_cli.add_argument('--no-network', action='store_true', default=False)

        args = parser.parse_args(argv)
        if args.command == 'discover':
            scope = Scope(args.platform, args.max_games, args.genre, args.developer_profile)
            result = discover(load_file(args.file), scope)
            print(json.dumps(result.to_dict(), ensure_ascii=False))
            return 0

        if args.command == 'scout':
            report = run_market_scout(
                provider=args.provider,
                genre=getattr(args, 'genre', 'all'),
                allow_network=not args.no_network,
            )
            print(json.dumps(report.to_dict(), ensure_ascii=False))
            return 0

        return 2
    except ValidationError as error:
        print(json.dumps({'error': {'code': error.code, 'message': str(error)}}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
