var sv_find_root = function sv_find_root (stats) {
    // looking for something that calls other functions,
    // but is never called itself.
    var callers = Immutable.Set.fromKeys(stats);
    var callees = Immutable.Set();

    for (var key in stats) {
        callees = callees.union(Immutable.Set(stats[key]['children']));
    }

    // hopefully there's only one thing left...
    return callers.subtract(callees).toJS()[0];
}

var sv_build_heirarchy =
function sv_build_heirarchy(stats, root_name, depth, node_size, parent_name) {
    // build a JSON heirarchy from stats data suitable for use with
    // a D3 partition.
    var data = {};
    data['name'] = root_name;
    data['size'] = node_size;
    if (parent_name == null) {
        data['parent_name'] = root_name;
    } else {
        data['parent_name'] = parent_name;
    }
    data['cumulative'] = stats[root_name]['stats'][3];

    if (depth !== 0 && stats[root_name]['children'].length !== 0) {
        data['children'] = [];

        for (var i in stats[root_name]['children']) {
            var child_name = stats[root_name]['children'][i];
            var child = stats[child_name];
            var child_size = child['stats'][3] / stats[root_name]['stats'][3] * node_size;
            data['children'].push(
                sv_build_heirarchy(
                    stats, child_name, depth - 1, child_size, root_name));
        }

        // make a child representing the internal time of this function
        var child_time = _.reduce(
            stats[root_name]['children'],
            function (sum, child) {
                return sum + stats[child]['stats'][3];
            },
            0
        );
        data['children'].push({
            name: root_name,
            parent_name: root_name,
            cumulative: stats[root_name]['stats'][3],
            size: ((stats[root_name]['stats'][3] - child_time) /
                   stats[root_name]['stats'][3] * node_size)
        });
    }

    return data;
}
