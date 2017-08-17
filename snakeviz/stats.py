from __future__ import division

import os.path
from itertools import chain

from tornado.escape import xhtml_escape


def table_rows(stats):
    """
    Generate a list of stats info lists for the snakeviz stats table.

    Each list will be a series of strings of:

    calls tot_time tot_time_per_call cum_time cum_time_per_call file_line_func

    """
    rows = []

    for k, v in stats.stats.items():
        flf = xhtml_escape('{0}:{1}({2})'.format(
            os.path.basename(k[0]), k[1], k[2]))
        name = '{0}:{1}({2})'.format(*k)

        if v[0] == v[1]:
            calls = str(v[0])
        else:
            calls = '{1}/{0}'.format(v[0], v[1])

        fmt = '{0:.4g}'.format

        tot_time = fmt(v[2])
        cum_time = fmt(v[3])
        tot_time_per = fmt(v[2] / v[0]) if v[0] > 0 else 0
        cum_time_per = fmt(v[3] / v[0]) if v[0] > 0 else 0

        rows.append(
            [[calls, v[1]], tot_time, tot_time_per,
             cum_time, cum_time_per, flf, name])

    return rows


def json_stats(stats):
    """
    Convert the all_callees data structure to something compatible with
    JSON. Mostly this means all keys need to be strings.

    """
    keyfmt = '{0}:{1}({2})'.format

    def _replace_keys(d):
        return dict((keyfmt(*k), v) for k, v in d.items())

    stats.calc_callees()

    nstats = {}

    for k, v in stats.all_callees.items():
        nk = keyfmt(*k)
        nstats[nk] = {}
        nstats[nk]['children'] = dict(
            (keyfmt(*ck), list(cv)) for ck, cv in v.items())
        nstats[nk]['stats'] = list(stats.stats[k][:4])
        nstats[nk]['callers'] = dict(
            (keyfmt(*ck), list(cv)) for ck, cv in stats.stats[k][-1].items())
        nstats[nk]['display_name'] = keyfmt(os.path.basename(k[0]), k[1], k[2])

    # remove anything that both never called anything and was never called
    # by anything.
    # this is profiler cruft.
    no_calls = set(k for k, v in nstats.items() if not v['children'])
    called = set(chain.from_iterable(
        d['children'].keys() for d in nstats.values()))
    cruft = no_calls - called

    for c in cruft:
        del nstats[c]

    return nstats
