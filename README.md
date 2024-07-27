# dqdl

dqdl ("Dune Query DownLoader") is a simple tool that downloads
[Dune](https://dune.com/) query result.

## Quickstart

Let's fetch the result of [query #3945714](https://dune.com/queries/3945714) –
a simple table that lists the number of smart contracts created on each chain
over the last 7 days.
First, install `dqdl` from PyPI:

```shell
pip install dqdl
```

Ensure that there is an `.env` file in the current working directory
with the following line in it:

```env
DUNE_API_KEY=YourDuneAPIKeyHere
```

(Need an API key?  Sign up and log into [Dune](https://dune.com/),
then [create your own key](https://dune.com/settings/api).)

Then run:

```shell
dqdl 3945714
```

The result should be saved in `3945714.csv` in the current directory:

```
$ head -5 3945714.csv 
blockchain,count
polygon,1376013.0
base,758165.0
optimism,588968.0
bnb,80817.0
```

## Usage

```
dqdl [-k SPEC] [-e FILE] [-E] [-o FILE] [-f FORMAT] QUERY
```

`QUERY` is the query number,
that is, the `XXXXXX` part in `https://dune.com/queries/XXXXXXX`.

### Specifying API key

`dqdl` requires a Dune API key
and by default reads one from the environment variable named `DUNE_API_KEY`.

Use `-k SPEC` to specify somewhere else to read the key; see
[openssl-passphrase-options(1)](https://docs.openssl.org/3.3/man1/openssl-passphrase-options/)
for the `SPEC` syntax.

### API key in `.env`

If the API key is from an environment variable (as in the default)
and the variable does not exist in the environment, `dqdl` looks it up in
a file named `.env` in the current directory—if one exists.
This "dotenv" file contains environment variables in the `NAME=VALUE` format,
one per line.

You can choose another file instead of `.env` with `-e FILE`.
Note: absence of this file is silently ignored, so beware typos!

If you want to avoid using the `.env` file even if one exists,
you can disable dotenv processing altogether with `-E`.

### Output location

The result is saved into a file named after the query number and the format,
e.g. `3945714.csv`.
The filename can be changed with `-o FILE` (`-o -` means stdout).

### Output format

By default, the output is saved in `csv`
([comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values))
format.

You can change the output format with `-f FORMAT`.
The `FORMAT` may be `csv` or `pqt`
([Apache Parquet](https://parquet.apache.org/)).

## Limitation

`dqdl` loads the entire query result in memory (for now),
and may fail if the result is too big to fit in memory.
