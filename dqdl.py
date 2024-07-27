__version__ = '0.1.0'

import argparse
import logging
import os
import sys
from enum import auto, StrEnum
from pathlib import Path

import dotenv
import pandas as pd
from dune_client.client import DuneClient

_logger = logging.getLogger(__name__)


class Format(StrEnum):
    CSV = auto()
    PQT = auto()


DEFAULT_FORMAT = Format.CSV


def read_pass(arg: str) -> str:
    match arg.split(':', 1):
        case ("pass", password):
            return password
        case ("env", var):
            return os.environ[var]
        case ("file", pathname):
            with open(pathname, "r") as f:
                return f.read()
        case ("fd", number):
            with os.fdopen(int(number), "r") as f:
                return f.read()
        case ("stdin", ):
            return sys.stdin.read()
        case _:
            raise ValueError("invalid password source {arg!r}")


def main():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', metavar='FILE', type=Path,
                        help=f"""output filename (default: query number, with
                                 a format-specific suffix such as .csv)""")
    parser.add_argument('--format', '-f', metavar='FORMAT', type=Format,
                        default=DEFAULT_FORMAT,
                        help=f"""output format; one of: {', '.join(Format)}
                                 (default: {DEFAULT_FORMAT})""")
    parser.add_argument('--api-key', '-k', metavar='SPEC',
                        default='env:DUNE_API_KEY',
                        help=f"""Dune API key spec
                                 (default: env:DUNE_API_KEY)""")
    parser.add_argument('--dotenv', '-e', metavar='FILE', type=Path,
                        default=Path('.env'),
                        help=f"""dotenv filename (default: .env)""")
    parser.add_argument('--no-dotenv', '-E', dest='dotenv',
                        action='store_const', const=None,
                        help=f"""disable dotenv processing""")
    parser.add_argument('query', metavar='QUERY', type=int,
                        help=f"""Dune query number""")
    args = parser.parse_args()
    if args.dotenv is not None:
        dotenv.load_dotenv(args.dotenv)
    output = args.output or f'{args.query}.{args.format}'
    api_key = read_pass(args.api_key)
    client = DuneClient(api_key=api_key)
    df: pd.DataFrame = client.get_latest_result_dataframe(args.query)
    if output == '-':
        output = sys.stdout
    match args.format:
        case Format.CSV:
            df.to_csv(output, index=False)
        case Format.PQT:
            df.to_parquet(output)
        case _:
            raise NotImplementedError(f"unknown format {args.format}")


if __name__ == '__main__':
    sys.exit(main())
