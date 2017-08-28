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
        var possible_roots = diff.toJS();
    } else {
        var possible_roots = _.keys(stats);
    }

    // if more than one potential root found, fall back on finding the thing
    // with the most cummulative time
    return _.maxBy(possible_roots, function (s) {
        return stats[s]['stats'][3];
    });
};


// Returns the hierarchy depth value from the depth <select> element
var sv_hierarchy_depth = function sv_hierarchy_depth() {
    return parseInt($('#sv-depth-select').val(), 10);
};


// Returns the hierarchy cutoff value from the cutoff <select> element
// This value is used to prune elements when building the call tree:
// if a child's cumulative time is less than this fraction of the parent
// then the program skips the descent into that child.
var sv_hierarchy_cutoff = function sv_hierarchy_cutoff() {
    return parseFloat($('#sv-cutoff-select').val());
};


// Configures the call stack button's settings and appearance
// for when the call stack is hidden.
var sv_call_stack_btn_for_show = function sv_call_stack_btn_for_show() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_show_call_stack);
    btn.removeClass('btn-active');
};


// Configures the call stack button's settings and appearance
// for when the call stack is visible.
var sv_call_stack_btn_for_hide = function sv_call_stack_btn_for_hide() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_hide_call_stack);
    btn.addClass('btn-active');
};


// Items on the call stack can include directory names that we want
// to remove for display in the call stack list.
var sv_item_name = function sv_item_name (name) {
    var slash = name.lastIndexOf('/');
    var rename = name;
    if (slash !== -1) {
        rename = name.slice(slash + 1);
    }
    return rename;
};


// Builds a list of div elements, each of which contain a number and
// a function description: file name:line number(function name)
var sv_call_tpl = _.template('<div><span><%= i %>.&nbsp;</span><span><%- name %></span></div>');
var sv_call_stack_list = function sv_call_stack_list(call_stack) {
    var calls = [];
    // the call stack list comes in ordered from root -> leaf,
    // but we want to display it leaf -> root, so we iterate over call_stack
    // in reverse here.
    for (var i = call_stack.length - 1; i >= 0; i--) {
        (function () {
            var index = i;
            var name = call_stack[i];
            var parent_name = (i > 0) ? call_stack[i-1] : null;
            calls.push($(sv_call_tpl(
                {'name': sv_item_name(name), 'i': index}
            )).click(function () {
                sv_draw_vis(name, parent_name);
                sv_call_stack = sv_call_stack.slice(0, index+1);
                sv_update_call_stack_list();
                if (name !== sv_root_func_name) {
                    $('#resetbutton-zoom').prop('disabled', false);
                } else {
                    $('#resetbutton-zoom').prop('disabled', true);
                }
            }));
        })()
    }
    return calls;
};


// update the displayed call stack list
var sv_update_call_stack_list = function sv_update_call_stack_list() {
    var calls = sv_call_stack_list(sv_call_stack);
    var div = $('#sv-call-stack-list');
    div.children().remove();
    div.append(calls);
    return div;
};


// make the call stack list visible
var sv_show_call_stack = function sv_show_call_stack() {
    sv_call_stack_btn_for_hide();
    var div = $('#sv-call-stack-list');
    div.css('max-height', get_sunburst_render_params()["radius"] * 1.5);
    div.show();
};


// hide the call stack list
var sv_hide_call_stack = function sv_hide_call_stack() {
    var div = $('#sv-call-stack-list');
    div.hide();
    sv_call_stack_btn_for_show();
};


// show the information div
var sv_show_info_div = function sv_show_info_div() {
    $('#sv-info-div').show();
};


// hide the information div
var sv_hide_info_div = function sv_hide_info_div() {
    $('#sv-info-div').hide();
};


// Show the "app is working" indicator
var sv_show_working = function sv_show_working() {
    $('#working-spinner').show();
};


// Hide the "app is working" indicator
var sv_hide_working = function sv_hide_working() {
    $('#working-spinner').hide();
};


// Make the worker and sv_draw_vis function
var sv_make_worker = function sv_make_worker() {
    var URL = URL || window.URL || window.webkitURL;
    var blob = new Blob(
        [$('#hierarchy-worker').text()], {'type': 'text/javascript'});
    var blobURL = URL.createObjectURL(blob);
    var sv_worker = new Worker(blobURL);

    sv_worker.onmessage = function (event) {
        var json = JSON.parse(event.data);
        if (cache_key != null) {
            sv_json_cache[cache_key] = json;
        }
        redraw_vis(json);
        _.defer(sv_hide_working);
    };

    sv_worker.onerror = function (event) {
        sv_show_error_msg();
        console.log(event);
        sv_cycle_worker();
        sv_hide_working();
    };

    sv_end_worker = function () {
        sv_worker.terminate();
        URL.revokeObjectURL(blobURL);
        sv_hide_working();
    };

    return sv_worker;
};


var sv_cycle_worker = function sv_cycle_worker() {
    sv_end_worker();
    sv_worker = sv_make_worker();
};


var sv_draw_vis = function sv_draw_vis(root_name, parent_name) {
    sv_show_working();
    var message = {
        'depth': sv_hierarchy_depth(),
        'cutoff': sv_hierarchy_cutoff(),
        'name': root_name,
        'parent_name': parent_name,
        'url': window.location.origin
    };

    cache_key = JSON.stringify(message);
    if (_.has(sv_json_cache, cache_key)) {
        redraw_vis(sv_json_cache[cache_key]);
        sv_hide_working();
    } else {
        sv_worker.postMessage(message);
    }
};


// An error message for when the worker fails building the call tree
var sv_show_error_msg = function sv_show_error_msg() {
    var radius = get_sunburst_render_params()["radius"];
    $('#sv-error-div')
        .css('top', window.innerHeight / 2 - radius)
        .css('left', window.innerWidth / 2 - radius)
        .width(radius * 2)
        .show();
};


var sv_hide_error_msg = function sv_hide_error_msg() {
    $('#sv-error-div').hide();
};
$('#sv-error-close-div').on('click', sv_hide_error_msg);
