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
            error = 'There was an error parsing {0} with pstats.'
            error = error.format(filename)
            self.render('upload.html', error=error)

        else:
            self.redirect('viz/' + filename)


class JSONHandler(handler.Handler):
    def get(self, prof_name):
        if self.request.path.startswith('/json/file/'):
            if self.settings['single_user_mode']:
                if prof_name[0] != '/':
                    prof_name = '/' + prof_name
                filename = os.path.abspath(prof_name)
            else:
                # TODO: Raise a 404 error here
                pass
        else:
            filename = storage_name(prof_name)

        s = prof_to_json(filename)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(s)


def prof_to_json(prof_name):
    loader = pstatsloader.PStatsLoader(prof_name)

    d = stats_to_tree_dict(loader.tree.children[0])

    return json.dumps(d, indent=1)


def stats_to_tree_dict(node, parent=None, parent_size=None,
                       recursive_seen=None):
    # recursive_seen prevents us from repeatedly traversing
    # recursive structures. only want to show the first set.
    if recursive_seen is None:
        recursive_seen = set()

    d = {}

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

        if node.recursive > node.calls:
            recursive_seen.add(node)

    if parent:
        if isinstance(parent, pstatsloader.PStatGroup):
            if parent.cummulative:
                d['size'] = node.cummulative / parent.cummulative * parent_size
            else:
                d['size'] = 0
        else:
            d['size'] = parent.child_cumulative_time(node) * parent_size
    else:
        d['size'] = 1000

    if node.children:
        d['children'] = []
        for child in node.children:
            if child not in recursive_seen:
                child_dict = stats_to_tree_dict(child, node, d['size'],
                                                recursive_seen)
                d['children'].append(child_dict)

        if d['children']:
            # make a "child" that represents the internal time of this function
            children_sum = sum(c['size'] for c in d['children'])

            if children_sum > d['size']:
                for child in d['children']:
                    child['size'] = child['size'] / children_sum * d['size']

            elif children_sum < d['size']:

                d_internal = {'name': node.name,
                              'filename': node.filename,
                              'directory': node.directory,
                              'size': d['size'] - children_sum}

                if isinstance(node, pstatsloader.PStatRow):
                    d_internal['calls'] = node.calls
                    d_internal['recursive'] = node.recursive
                    d_internal['local'] = node.local
                    d_internal['localPer'] = node.localPer
                    d_internal['cummulative'] = node.cummulative
                    d_internal['cummulativePer'] = node.cummulativePer
                    d_internal['line_number'] = node.lineno

                d['children'].append(d_internal)
        else:
            del d['children']

    if node in recursive_seen:
        recursive_seen.remove(node)

    return d
