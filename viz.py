import pstats
import StringIO

import handler
import upload

class SunburstHandler(handler.Handler):
    def get(self, profile_name):
        # get the print_stats output from pstats
        # sorted with most cumulative time at the top
        stats_stream = StringIO.StringIO()
        stats = pstats.Stats(upload.storage_name(profile_name),
            stream=stats_stream)
        stats.strip_dirs()
        stats.sort_stats('cum').print_stats()

        # get just the table rows, none of the header or footer
        data = stats_stream.getvalue().strip()
        key_str = 'filename:lineno(function)\n'
        data_index = data.find(key_str) + len(key_str)

        rows = data[data_index:].split('\n')
        rows = [r.split() for r in rows]

        self.render('sunburst.html', profile_name=profile_name, stats_rows=rows)
