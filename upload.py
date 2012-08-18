import pstats
import json
import tempfile
import os

import pstatsloader
import handler


def storage_name(filename):
    return os.path.join(tempfile.gettempdir(), filename)


class UploadHandler(handler.Handler):
    def get(self):
        self.render('upload.html')

    def post(self):
        filename = self.request.files['profile'][0]['filename']
        sfilename = storage_name(filename)

        # save the stats info to a file so it can be loaded by pstats
        with open(sfilename, 'wb') as f:
            f.write(self.request.files['profile'][0]['body'])

        # test whether this can be opened with pstats
        try:
            pstats.Stats(sfilename)

        except:
            os.remove(sfilename)
            error = 'There was an error parsing {} with pstats.'
            error = error.format(filename)
            self.render('upload.html', error=error)

        else:
            self.redirect('sunburst/' + filename)


class JSONHandler(handler.Handler):
    def get(self, prof_name):
        s = self.prof_to_json(storage_name(prof_name))

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(s)

    def prof_to_json(self, prof_name):
        loader = pstatsloader.PStatsLoader(prof_name)

        d = self.stats_to_tree_dict({}, loader.tree.children[0])

        return json.dumps(d, indent=1)

    def stats_to_tree_dict(self, d, node, parent=None, pdict=None):
        d['name'] = node.name
        d['filename'] = node.filename
        d['directory'] = node.directory

        if isinstance(node, pstatsloader.PStatRow):
            d['calls'] = node.calls
            d['recursive'] = node.recursive
            d['local'] = node.local
            d['localPer'] = node.localPer
            d['cummulative'] = node.cummulative
            d['cummulativePer'] = node.cummulativePer
            d['line_number'] = node.lineno

        if parent:
            if isinstance(parent, pstatsloader.PStatGroup):
                if parent.cummulative:
                    d['size'] = node.cummulative / parent.cummulative * pdict['size']
                else:
                    d['size'] = 0
            else:
                d['size'] = parent.child_cumulative_time(node) * pdict['size']
        else:
            d['size'] = 1000

        if node.children:
            d['children'] = []
            for child in node.children:
                d['children'].append(self.stats_to_tree_dict({}, child, node, d))

            # make a "child" that represents the internal time of this function
            #print d['children']
            children_size = sum(c['size'] for c in d['children'])
            #assert children_size <= 1, 'Children size is unrealistically big! ' + str(children_size)

            d_internal = {'name': node.name,
                          'filename': node.filename,
                          'directory': node.directory,
                          'size': d['size'] - children_size}

            if isinstance(node, pstatsloader.PStatRow):
                d_internal['calls'] = node.calls
                d_internal['recursive'] = node.recursive
                d_internal['local'] = node.local
                d_internal['localPer'] = node.localPer
                d_internal['cummulative'] = node.cummulative
                d_internal['cummulativePer'] = node.cummulativePer
                d_internal['line_number'] = node.lineno

            d['children'].append(d_internal)

        return d
