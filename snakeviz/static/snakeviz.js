var STYLE_SELECT = '#sv-style-select';
var DEPTH_SELECT = '#sv-depth-select';
var CUTOFF_SELECT = '#sv-cutoff-select';
var CALL_STACK = '#sv-call-stack-list';

// Look for something that calls other functions,
// but is never called itself.
var sv_find_root = function(stats) {
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
};


// Returns the heirarchy depth value from the depth <select> element
var sv_heirarchy_depth = function() {
    return parseInt($(DEPTH_SELECT).val(), 10);
};


// Returns the heirarchy cutoff value from the cutoff <select> element
// This value is used to prune elements when building the call tree:
// if a child's cumulative time is less than this fraction of the parent
// then the program skips the descent into that child.
var sv_heirarchy_cutoff = function() {
    return parseFloat($(CUTOFF_SELECT).val());
};


// Configures the call stack button's settings and appearance
// for when the call stack is hidden.
var sv_call_stack_btn_for_show = function() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_show_call_stack);
    btn.removeClass('btn-active');
};


// Configures the call stack button's settings and appearance
// for when the call stack is visible.
var sv_call_stack_btn_for_hide = function() {
    var btn = $('#sv-call-stack-btn');
    btn.on('click', sv_hide_call_stack);
    btn.addClass('btn-active');
};


// Items on the call stack can include directory names that we want
// to remove for display in the call stack list.
var sv_item_name = function(name) {
    var slash = Math.max(name.lastIndexOf('/'),name.lastIndexOf('\\'));
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
                	resetButton.enable();
                } else {
                	resetButton.disable();
               }
            }));
        })()
    }
    return calls;
};


// update the displayed call stack list
var sv_update_call_stack_list = function() {
    var calls = sv_call_stack_list(sv_call_stack);
    var div = $(CALL_STACK);
    div.children().remove();
    div.append(calls);
    return div;
};


// make the call stack list visible
var sv_show_call_stack = function() {
    sv_call_stack_btn_for_hide();
    var div = $(CALL_STACK);
    div.css('max-height', $("#chart").height());
    div.show();
};


// hide the call stack list
var sv_hide_call_stack = function() {
    var div = $(CALL_STACK);
    div.hide();
    sv_call_stack_btn_for_show();
};

// show the information div
var sv_show_info_div = function() {
    $('#sv-info-div').show();
};

// hide the information div
var sv_hide_info_div = function() {
    $('#sv-info-div').hide();
};

// Show the "app is working" indicator
var sv_show_working = function() {
    $('#working-spinner').show();
};

// Hide the "app is working" indicator
var sv_hide_working = function() {
    $('#working-spinner').hide();
};

// Make the worker and sv_draw_vis function
var sv_make_worker = function() {
    var URL = URL || window.URL || window.webkitURL;
    var blob = new Blob(
        [$('#heirarchy-worker').text()], {'type': 'text/javascript'});
    var blobURL = URL.createObjectURL(blob);
    var sv_worker = new Worker(blobURL);

    sv_worker.onmessage = function (event) {
        cache_key = JSON.stringify(event.data);        
        if (!(_.has(sv_json_cache, cache_key))) {
        	var json = JSON.parse(event.data);
            sv_json_cache[cache_key] = json;
        }
        clear_and_redraw_vis(sv_json_cache[cache_key]);
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


var sv_cycle_worker = function() {
    sv_end_worker();
    sv_worker = sv_make_worker();
};


var sv_draw_vis = function(root_name, parent_name) {
    sv_show_working();
    var message = buildMessage(root_name,parent_name);
	sv_worker.postMessage(message);
    sv_hide_working();
};

var buildMessage = function(rootName, parentName,initialRun){
	if (initialRun){
		depth = 10000;
		cutoff = 0;
	}else{
		depth = sv_heirarchy_depth();
		cutoff = sv_heirarchy_cutoff();
	}
	return {
        'depth': depth,
        'cutoff': cutoff,
        'name': rootName,
        'parent_name': parentName,
        'url': window.location.origin
    };
}

// An error message for when the worker fails building the call tree
var sv_show_error_msg = function() {
    $('#sv-error-div')
        .css('top', window.innerHeight / 3)
        .css('left', window.innerWidth / 4)
        .width(window.innerWidth / 2)
        .show();
};

var sv_hide_error_msg = function() {
    $('#sv-error-div').hide();
};
$('#sv-error-close-div').on('click', sv_hide_error_msg);
