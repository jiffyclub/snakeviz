var sv_find_root = function sv_find_root (stats) {
    // looking for something that calls other functions,
    // but is never called itself.
    var callers = Immutable.Set.fromKeys(stats);
    var callees = Immutable.Set();

    for (var key in stats) {
        callees = callees.union(Immutable.Set.fromKeys(stats[key]['children']));
    }

    // hopefully there's only one thing left...
    return callers.subtract(callees).toJS()[0];
}

var sv_build_heirarchy =
function sv_build_heirarchy(
        stats, root_name, depth, node_size, parent_name, call_stack) {
    // build a JSON heirarchy from stats data suitable for use with
    // a D3 partition.
    if (call_stack == null) {
        var call_stack = Immutable.Set([root_name]);
    } else {
        var call_stack = call_stack.add(root_name);
    }

    var data = {};
    data['name'] = root_name;
    data['size'] = node_size;
    data['cumulative'] = stats[root_name]['stats'][3];
    if (parent_name == null) {
        data['parent_name'] = root_name;
        var parent_time = data['cumulative'];
    } else {
        data['parent_name'] = parent_name;
        var parent_time = stats[root_name]['callers'][parent_name][3];
    }

    if (depth !== 0 && _.size(stats[root_name]['children']) !== 0) {
        data['children'] = [];

        for (var child_name in stats[root_name]['children']) {
            // make sure we're not recursing into a function
            // that's already on the stack
            if (call_stack.contains(child_name)) {
                continue;
            }

            var child_time = stats[child_name]['callers'][root_name][3];
            var child_size = child_time / parent_time * node_size;
            data['children'].push(
                sv_build_heirarchy(
                    stats, child_name, depth - 1, child_size, root_name, call_stack));
        }

        // do all the children add up to be larger than the parent?
        var size_of_children = _.reduce(
            data['children'],
            function (sum, child) {
                return sum + child['size'];
            },
            0
        );
        // if so, normalize them to the size of this node
        if (size_of_children > node_size) {
            for (var i in data['children']) {
                data['children'][i]['size'] =
                    data['children'][i]['size'] / size_of_children * node_size;
            }
        } else {
            // make a child representing the internal time of this function
            var time_in_children = _.reduce(
                stats[root_name]['children'],
                function (sum, child) {
                    return sum + child[3];
                },
                0
            );
            data['children'].push({
                name: root_name,
                parent_name: root_name,
                cumulative: stats[root_name]['stats'][3],
                size: (parent_time - time_in_children) / parent_time * node_size
            });
        }
    }

    return data;
}

var sv_heirarchy_depth = function sv_heirarchy_depth() {
    return parseInt($('#sv-depth-select').val());
}
