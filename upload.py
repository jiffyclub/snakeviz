import json

import pstatsloader
import handler

class UploadHandler(handler.Handler):
    def get(self):
        self.render('upload.html')

    def post(self):
        filename = self.request.files['profile'][0]['filename']

        # save the stats info to a file so it can be loaded by pstats
        with open(filename, 'wb') as f:
            f.write(self.request.files['profile'][0]['body'])

        self.redirect(filename + '.json')


class JSONHandler(handler.Handler):
    def get(self, prof_name):
        s = self.prof_to_json(prof_name)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(s)

    def prof_to_json(self, prof_name):
        loader = pstatsloader.PStatsLoader(prof_name)

        d = self.stats_to_tree_dict({}, loader.tree.children[0])

        return json.dumps(d, indent=1)

    def stats_to_tree_dict(self, d, node):
        d['name'] = node.name
        d['size'] = 1
        if node.children:
            d['children'] = []
            for child in node.children:
                d['children'].append(self.stats_to_tree_dict({}, child))
        return d
