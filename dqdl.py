__version__ = '0.1.1'

import argparse
import logging
import sys
from enum import auto, StrEnum
from pathlib import Path

import dotenv
import pandas as pd
import passarg
from dune_client.client import DuneClient

_logger = logging.getLogger(__name__)


class Format(StrEnum):
    CSV = auto()
    PQT = auto()


def main():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    defaults = dict(
        format=Format.CSV,
        api_key='env:DUNE_API_KEY',
        dotenv=Path('.env'),
    )
    parser.set_defaults(**defaults)
    parser.add_argument('-o', '--output', metavar='FILE', type=Path,
                        help=f"""output filename
                                 (default: query number, with format-specific
                                 suffix such as .{defaults['format']})""")
    parser.add_argument('-f', '--format', metavar='FORMAT', type=Format,
                        help=f"""output format; one of: {', '.join(Format)}
                                 (default: {defaults['format']})""")
    parser.add_argument('-k', '--api-key', metavar='SPEC',
                        help=f"""Dune API key spec
                                 (default: {defaults['api_key']})""")
    parser.add_argument('-e', '--dotenv', metavar='FILE', type=Path,
                        help=f"""dotenv filename
                                 (default: {defaults['dotenv']})""")
    parser.add_argument('-E', '--no-dotenv', dest='dotenv',
                        action='store_const', const=None,
                        help=f"""disable dotenv processing""")
    parser.add_argument('query', metavar='QUERY', type=int,
                        help=f"""Dune query number""")
    args = parser.parse_args()
    if args.dotenv is not None:
        dotenv.load_dotenv(args.dotenv)
    output = args.output or f'{args.query}.{args.format}'
    with passarg.reader() as read_pass:
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
