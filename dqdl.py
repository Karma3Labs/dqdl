__version__ = '0.1.1'

import argparse
import logging
import sys
from datetime import datetime, timezone
from enum import auto, StrEnum
from pathlib import Path
from typing import Any

import dotenv
import pandas as pd
import passarg
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dune_client.types import ParameterType, QueryParameter
from iso8601 import parse_date
from requests.exceptions import HTTPError

_logger = logging.getLogger(__name__)

log_levels = {n.lower(): v
              for n, v in logging.getLevelNamesMapping().items()
              if n not in ('NOTSET', 'WARN')}


class Format(StrEnum):
    CSV = auto()
    PQT = auto()


def param(qp: str) -> QueryParameter:
    """Parse and return a Dune query parameter."""
    nt, s = qp.split('=', 1)
    try:
        n, ts = nt.rsplit(':', 1)
    except ValueError:
        n = nt
        t, v = guess_qp_type(s)
        _logger.info(f"guessed type {t.value} for parameter {n}; "
                     f"consider specifying it, i.e. {n}:{t.value}={s}")
    else:
        t = ParameterType.from_string(ts)
        v = parse_qp_value(t, s)
    return QueryParameter(n, t, v)


def parse_date_into_utc(v: str) -> datetime:
    return parse_date(v).astimezone(timezone.utc)


def guess_qp_type(v: str) -> tuple[ParameterType, Any]:
    """Guess the Dune query parameter type of the given value."""
    try:
        return ParameterType.DATE, parse_date_into_utc(v)
    except ValueError:
        pass
    try:
        return ParameterType.NUMBER, int(v)
    except ValueError:
        pass
    try:
        return ParameterType.NUMBER, float(v)
    except ValueError:
        pass
    if ',' in v:
        return ParameterType.ENUM, v
    return ParameterType.TEXT, v


def parse_qp_value(t: ParameterType, v: str) -> Any:
    """Parse a Dune query parameter value of the given type."""
    match t:
        case ParameterType.TEXT:
            return v
        case ParameterType.NUMBER:
            try:
                return int(v)
            except ValueError:
                return float(v)
        case ParameterType.DATE:
            return parse_date_into_utc(v)
        case ParameterType.ENUM:
            return v


def log_level(name: str) -> int:
    try:
        return log_levels[name]
    except KeyError as e:
        raise ValueError from e


def main():
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    defaults = dict(
        format=Format.CSV,
        api_key='env:DUNE_API_KEY',
        dotenv=Path('.env'),
    )
    log_level_names = [kv[0]
                       for kv in sorted(log_levels.items(),
                                        key=lambda kv: kv[1])]
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
    parser.add_argument('-r', '--run', action='store_true', default=False,
                        help="""actually run the query
                                (default is to fetch existing result)""")
    parser.add_argument('--log-level', metavar='LEVEL',
                        type=log_level,
                        help=f"""enable log messages at LEVEL or higher; 
                                 one of: {', '.join(log_level_names)}""")
    parser.add_argument('query', metavar='QUERY', type=int,
                        help=f"""Dune query number""")
    parser.add_argument('params', metavar='NAME[:TYPE]=VALUE',
                        type=param, nargs='*',
                        help=f"""Dune query parameters (TYPE is one of:
                                 {', '.join(v.value
                                            for v in ParameterType)})""")
    args = parser.parse_args()
    if args.log_level is not None:
        _logger.setLevel(args.log_level)
    if args.dotenv is not None:
        dotenv.load_dotenv(args.dotenv)
    output = args.output or f'{args.query}.{args.format}'
    with passarg.reader() as read_pass:
        api_key = read_pass(args.api_key)
    client = DuneClient(api_key=api_key)
    if args.log_level is not None:
        client.logger.setLevel(args.log_level)
    q = QueryBase(query_id=args.query, params=args.params)
    try:
        df: pd.DataFrame = client.get_latest_result_dataframe(q)
    except HTTPError as e:
        if e.response.status_code != 404 or not args.run:
            raise
        df: pd.DataFrame = client.run_query_dataframe(q)
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
