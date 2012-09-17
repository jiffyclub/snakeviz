"""
This module contains the handler and supporting functions for the primary
visualization page.

"""

import os
from collections import namedtuple

from . import pstatsloader
from . import handler
from . import upload


# a structure to represent all of the profile data on a particular function
# the viz.html template is expecting a list of these so it can build its
# stats table.
StatsRow = namedtuple('StatsRow', ['calls_value', 'calls_str',
                                   'tottime', 'tottime_str',
                                   'tottime_percall', 'tottime_percall_str',
                                   'cumtime', 'cumtime_str',
                                   'cumtime_percall', 'cumtime_percall_str',
                                   'file_line_func'])


def stats_rows(filename):
    """
    Build a list of StatsRow objects that will be used to make the
    profile stats table beneath the profile visualization.

    Parameters
    ----------
    filename : str
        Name of profiling output as made by Python's built-in profilers.

    """
    time_fmt = '{0:>12.6g}'

    loader = pstatsloader.PStatsLoader(filename)

    rows = []

    for r in loader.rows.itervalues():
        if isinstance(r, pstatsloader.PStatRow):
            calls_value = r.recursive
            if r.recursive > r.calls:
                calls_str = '{0}/{1}'.format(r.recursive, r.calls)
            else:
                calls_str = str(r.calls)
            tottime = r.local
            tottime_str = time_fmt.format(tottime)
            tottime_percall = r.localPer
            tottime_percall_str = time_fmt.format(tottime_percall)
            cumtime = r.cummulative
            cumtime_str = time_fmt.format(cumtime)
            cumtime_percall = r.cummulativePer
            cumtime_percall_str = time_fmt.format(cumtime_percall)
            file_line_func = '{0}:{1}({2})'.format(r.filename,
                                                   r.lineno,
                                                   r.name)
            rows.append(StatsRow(calls_value, calls_str,
                                 tottime, tottime_str,
                                 tottime_percall, tottime_percall_str,
                                 cumtime, cumtime_str,
                                 cumtime_percall, cumtime_percall_str,
                                 file_line_func))

    return rows


class VizHandler(handler.Handler):
    """
    Handler for the main visualization page. Renders viz.html.

    """
    def get(self, profile_name):
        if self.request.path.startswith('/viz/file/'):
            if self.settings['single_user_mode']:
                # Allow opening arbitrary files by full filesystem path
                # WARNING!!! Obviously this must be disabled by default
                # TODO: Some modicum of error handling here as well...
                if profile_name[0] != '/':
                    profile_name = '/' + profile_name
                filename = os.path.abspath(profile_name)
                json_path = '/json/file%s.json' % profile_name
            else:
                # TODO: Raise a 404 error here
                pass
        else:
            filename = upload.storage_name(profile_name)
            json_path = '/json/%s.json' % filename

        rows = stats_rows(filename)

        self.render('viz.html', profile_name=profile_name, json_path=json_path,
                    stats_rows=rows)
