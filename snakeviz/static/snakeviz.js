// Look for something that calls other functions,
// but is never called itself.
var sv_find_root = function sv_find_root (stats) {
    var callers = Immutable.Set.fromKeys(stats);
    var callees = Immutable.Set();

    for (var key in stats) {
        callees = callees.union(Immutable.Set.fromKeys(stats[key]['children']));
    }

    var diff = callers.subtract(callees);
    if (diff.size !== 0) {
        // hopefully there's only one thing left...
        return diff.toJS()[0];
    } else {
        // fall back on finding the thing with the most
        // cummulative time
        return _.max(_.keys(stats), function (s) {
            return stats[s]['stats'][3];
        });
    }
    throw 'no root found';
}


// Take the embedded stats JSON and turn it into an object tree
// suitable for use with D3's partition/heirarchy machinery.
var sv_build_heirarchy =
function sv_build_heirarchy(
        stats, root_name, depth, node_size, parent_name, call_stack) {

    // We track the call stack both for display purposes and to avoid
    // displaying recursive calls.
    if (call_stack == null) {
        var call_stack = Immutable.Set([root_name]);
    } else {
        var call_stack = call_stack.add(root_name);
    }

    var data = {};
    data['name'] = root_name;
    data['display_name'] = stats[root_name]['display_name'];
    data['size'] = node_size;
    data['cumulative'] = stats[root_name]['stats'][3];
    if (parent_name == null) {
        // This should only happen once: for the root node.
        data['parent_name'] = root_name;
        var parent_time = data['cumulative'];
    } else {
        data['parent_name'] = parent_name;
        // the amount of time spent in root_name when it was called by parent_time
        var parent_time = stats[root_name]['callers'][parent_name][3];
    }

    if (depth !== 0 && _.size(stats[root_name]['children']) !== 0) {
        // figure out the child sizes
        // we do this here because it needs to be correct before
        // heading further into the call stack
        var child_sizes = {};
        var size_of_children = 0;

        for (var child_name in stats[root_name]['children']) {
            // the amount of time spent in a child when it was called by root_name
            var child_time = stats[child_name]['callers'][root_name][3];
            child_sizes[child_name] = child_time / parent_time * node_size;
            size_of_children += child_sizes[child_name];
        }

        // if the children add up to be larger than the parent
        // then normalize them to the parent size
        if (size_of_children > node_size) {
            for (var child_name in stats[root_name]['children']) {
                child_sizes[child_name] *= (node_size / size_of_children);
            }
        }

        data['children'] = [];

        for (var child_name in stats[root_name]['children']) {
            // make sure we're not recursing into a function
            // that's already on the stack
            if (call_stack.contains(child_name)) {
                continue;
            }


            data['children'].push(
                sv_build_heirarchy(
                    stats, child_name, depth - 1, child_sizes[child_name],
                    root_name, call_stack));
        }

        if (size_of_children < node_size) {
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
                display_name: data['display_name'],
                parent_name: data['parent_name'],
                cumulative: stats[root_name]['stats'][3],
                size: Math.max(
                    0, (parent_time - time_in_children) / parent_time * node_size)
            });
        }
    }

    return data;
}


// Returns the heirarchy depth value from the depth <select> element
var sv_heirarchy_depth = function sv_heirarchy_depth() {
    return parseInt($('#sv-depth-select').val());
}


// Configures the call stack button's settings and appearance
// for when the call stack is hidden.
var sv_call_stack_btn_for_show = function sv_call_stack_btn_for_show() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_show_call_stack);
    btn.removeClass('btn-active');
}


// Configures the call stack button's settings and appearance
// for when the call stack is visible.
var sv_call_stack_btn_for_hide = function sv_call_stack_btn_for_hide() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_hide_call_stack);
    btn.addClass('btn-active');
}


// Items on the call stack can include directory names that we want
// to remove for display in the call stack list.
var sv_item_name = function sv_item_name (name) {
    var slash = name.lastIndexOf('/');
    var rename = name;
    if (slash !== -1) {
        rename = name.slice(slash + 1);
    }
    return rename;
}


// Builds a list of div elements, each of which contain a number and
// a function description: file name:line number(function name)
var sv_call_tpl = _.template('<div><%= i %>. <%- name %></div>');
var sv_call_stack_list = function sv_call_stack_list(call_stack) {
    var calls = [];
    // the call stack list comes in ordered from root -> leaf,
    // but we want to display it leaf -> root, so we iterate over call_stack
    // in reverse here.
    for (var i = call_stack.length - 1; i >= 0; i--) {
        calls.push(
            sv_call_tpl(
                {'name': sv_item_name(call_stack[i]), 'i': i}));
    };
    return calls;
}


// update the displayed call stack list
var sv_update_call_stack_list = function sv_update_call_stack_list() {
    var calls = sv_call_stack_list(sv_call_stack);
    var div = $('#sv-call-stack-list');
    div.children().remove();
    div.append(calls);
    return div;
}


// make the call stack list visible
var sv_show_call_stack = function sv_show_call_stack() {
    sv_call_stack_btn_for_hide();
    var div = $('#sv-call-stack-list');
    div.css('max-height', radius * 1.5);
    div.show();
}


// hide the call stack list
var sv_hide_call_stack = function sv_hide_call_stack() {
    var div = $('#sv-call-stack-list');
    div.hide();
    sv_call_stack_btn_for_show();
}


// show the information div
var sv_show_info_div = function sv_show_info_div() {
    $('#sv-info-div').show();
}


// hide the information div
var sv_hide_info_div = function sv_hide_info_div() {
    $('#sv-info-div').hide();
}
