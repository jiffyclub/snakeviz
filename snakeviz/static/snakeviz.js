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

var callStackObject = function(rootFunctionName){
	var self = this;
	var rootName = rootFunctionName;
	var _currentRoot = rootName;
	var _currentParent = null;
  var callStack = [rootName];
  var button = $('#sv-call-stack-btn');
  var listDiv = $(CALL_STACK);
  var callTemplate = _.template('<div><span><%= i %>.&nbsp;</span><span><%- name %></span></div>');
  
  this.currentRoot = function(){
  	return _currentRoot;
  };
  
  this.currentParent = function() {
  	return _currentParent;
  };
  this.currentStack = function(){
  	return callStack;
  };
  
  this.resetStack = function(){
  	callStack = [rootName];
  };
  
  this.show = function(){    	
  	button.on('click', self.hide);
  	button.removeClass('btn-active');
  	listDiv.css('max-height', $("#chart").height());
  	listDiv.show();
  };
  
  this.hide = function(){
  	button.on('click', self.show);
  	button.addClass('btn-active');
  	listDiv.hide();
  };
  
  this.updateDisplay = function(){
    var calls = makeDisplayList();
    listDiv.children().remove();
    listDiv.append(calls);
  };
  
  makeDisplayList = function(){
    // Builds a list of div elements, each of which contain a number and
  	// a function description: file name:line number(function name)
  	var calls = [];
    // the call stack list comes in ordered from root -> leaf,
    // but we want to display it leaf -> root, so we iterate over call_stack
    // in reverse here.
  	lengthStack = callStack.length - 1;
    for (var i = lengthStack; i >= 0; i--) {
      (function () {
        var index = i;
        var name = callStack[i];
        var parent_name = (i > 0) ? callStack[i-1] : null;
        var callStackLine = $(callTemplate(
        		{'name': sv_item_name(name), 'i': index}));
        // if we are at the root then there is no action on clicking
        // the stack
        if (i != lengthStack) {
              callStackLine.click(function () {
              	sv_draw_vis(name, parent_name);
              });
      };
      calls.push(callStackLine);
        }());
    }
  	return calls;
  	};
    	
  this.updateStack = function(functionName,parentName){   	
  	var new_root = functionName;
  	var new_parent_name = (functionName === rootName) ? null : parentName;
  	posParentInStack = callStack.indexOf(parentName);
  	posFunctionInStack = callStack.indexOf(functionName);
  	if (functionName === rootName) {
  		// check whether we need to do anything
      // (e.g. that the user hasn't clicked on the original root node)
  		self.resetStack();
  	} else if(posParentInStack>=0 && posFunctionInStack>=0){
  		// Check if stack contains the calls already
  		if (functionName === _.last(callStack)){
  			new_root = callStack[posParentInStack];
  			new_parent_name = callStack[posParentInStack-1];
  		}
		callStack = _.first(callStack,posFunctionInStack);
  	}else{
  		// need to construct a new call stack
  		// go up the tree until we hit the tip of the call stack
  		var local_stack = [new_root];
    	var thisNode = findData(functionName,parentName);
    	var thisParent = thisNode.parent;
	    while (thisParent.name != null) {
        if (thisParent.name === _.last(callStack)) {
          // extend the call stack with what we've accumulated
          local_stack.reverse();
          callStack = callStack.concat(local_stack);
          break;
        } else {
          local_stack.push(thisParent.name);
          thisParent = thisParent.parent;
        	}
    	}
    }
    self.updateDisplay();
    _currentRoot = new_root;
    _currentParent = new_parent_name;
  };
  
  this.checkResetButtonState = function(){
    // Activate the reset button if we aren't already at the root node
    // And deactivate it if this is the root node
    if (_currentRoot !== rootName) {
  	  resetButton.enable();
    } else {
  	  resetButton.disable();
    };    	
  };
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
  };
  
  sv_worker.onerror = function (event) {
    sv_show_error_msg();
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


var sv_draw_vis = function(root_name, parent_name,init) {
  sv_show_working();
  if (root_name != null){
    callStack.updateStack(root_name,parent_name);
    callStack.checkResetButtonState();
  }
  var message = buildMessage(callStack.currentRoot(),callStack.currentParent(),init);
  sv_worker.postMessage(message);
  _.defer(sv_hide_working);
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
};

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
