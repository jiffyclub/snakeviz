import os
import pstats
import StringIO

from . import handler
from . import upload

class SunburstHandler(handler.Handler):
    def get(self, profile_name):
        # get the print_stats output from pstats
        # sorted with most cumulative time at the top
        stats_stream = StringIO.StringIO()

        if self.request.path.startswith('/viz/file/'):
            if self.settings['single_user_mode']:
                # Allow opening arbitrary files by full filesystem path
                # WARNING!!! Obviously this must be disabled by default
                # TODO: Some modicum of error handling here as well...
                if profile_name[0] != '/':
                    profile_name = '/' + profile_name
                filename = os.path.abspath(profile_name)
            else:
                # TODO: Raise a 404 error here
                pass
        else:
            filename = upload.storage_name(profile_name)

        stats = pstats.Stats(filename, stream=stats_stream)
        stats.strip_dirs()
        stats.sort_stats('cum').print_stats()

        # get just the table rows, none of the header or footer
        data = stats_stream.getvalue().strip()
        key_str = 'filename:lineno(function)\n'
        data_index = data.find(key_str) + len(key_str)

        rows = data[data_index:].split('\n')
        rows = [r.split() for r in rows]

        self.render('viz.html', profile_name=profile_name, stats_rows=rows)
