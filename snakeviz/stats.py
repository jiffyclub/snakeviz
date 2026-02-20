import os.path
from itertools import chain
from pstats import Stats as _Stats
from typing import NamedTuple, TypeAlias, TypedDict

from tornado.escape import xhtml_escape


FuncKey: TypeAlias = tuple[str, int, str]
CallStats: TypeAlias = tuple[int, int, float, float]
Callers: TypeAlias = dict[FuncKey, CallStats]
StatsDict: TypeAlias = dict[FuncKey, tuple[int, int, float, float, Callers]]


class Stats(_Stats):
    """Wrapper for `pstats.Stats` adding some missing type annotation only"""

    all_callees: dict[FuncKey, Callers]
    stats: StatsDict


class TableCallStats(NamedTuple):
    calls: tuple[str, str]
    tot_time: str
    tot_time_per: str
    cum_time: str
    cum_time_per: str
    flf: str
    name: str


def table_rows(stats: Stats) -> list[TableCallStats]:
    """
    Generate a list of stats info lists for the snakeviz stats table.

    Each list will be a series of strings of:

    calls tot_time tot_time_per_call cum_time cum_time_per_call file_line_func

    """
    rows: list[TableCallStats] = []

    for k, v in stats.stats.items():
        flf = xhtml_escape('{}:{}({})'.format(
            os.path.basename(k[0]), k[1], k[2]))
        name = '{}:{}({})'.format(*k)

        if v[0] == v[1]:
            calls = str(v[0])
        else:
            calls = f'{v[1]}/{v[0]}'

        fmt = '{:.4g}'.format

        tot_time = fmt(v[2])
        cum_time = fmt(v[3])
        tot_time_per = fmt(v[2] / v[0]) if v[0] > 0 else '0'
        cum_time_per = fmt(v[3] / v[0]) if v[0] > 0 else '0'

        rows.append(TableCallStats(
            (calls, str(v[1])), tot_time, tot_time_per,
            cum_time, cum_time_per, flf, name))

    return rows


class JSONStatsNode(TypedDict):
    children: dict[str, CallStats]
    stats: CallStats
    callers: dict[str, CallStats]
    display_name: str


JSONStats: TypeAlias = dict[str, JSONStatsNode]


def json_stats(stats: Stats) -> JSONStats:
    """
    Convert the all_callees data structure to something compatible with
    JSON. Mostly this means all keys need to be strings.

    """
    keyfmt = '{}:{}({})'.format

    stats.calc_callees()

    nstats: JSONStats = {}

    for k, v in stats.all_callees.items():
        nk = keyfmt(*k)
        nstats[nk] = dict(
            children={keyfmt(*ck): cv for ck, cv in v.items()},
            stats=stats.stats[k][:4],
            callers={
                keyfmt(*ck): cv for ck, cv in stats.stats[k][-1].items()
            },
            display_name=keyfmt(os.path.basename(k[0]), k[1], k[2])
        )

    # remove anything that both never called anything and was never called
    # by anything.
    # this is profiler cruft.
    no_calls = {k for k, v in nstats.items() if not v['children']}
    called = set(chain.from_iterable(
        d['children'].keys() for d in nstats.values()))
    cruft = no_calls - called

    for c in cruft:
        del nstats[c]

    return nstats
