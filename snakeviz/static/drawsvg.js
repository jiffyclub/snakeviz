// This contains the code that renders and controls the visualization.

var DIMS = {
		"leftMargin": parseInt($('body').css('padding')) + parseInt($('body').css('margin')), 
		"rightMargin": 60,
		"topMargin":60,
		"widthInfo": 200,
};

var SVG_DIMS={
		width: window.innerWidth-DIMS["leftMargin"]-DIMS["widthInfo"]-DIMS["rightMargin"],
		height: .75 * (window.innerHeight-DIMS["topMargin"]),
	};

var LAYOUT_DICTIONARY={ 
	     sunburst: Sunburst, 
	     icicle: Icicle, 
	};

function  DrawStratergy(layout){
	this.layout = layout;
	this.layout.get_render_params();
};
DrawStratergy.prototype.draw= function(json){
	this.layout.draw(json);
};		

function DrawLayout() {
	this.params={};
};
DrawLayout.prototype.get_render_params = function(){};
DrawLayout.prototype.draw = function(json){
	pixcelLimit = this.params["minPixel"];
	var nodes = this.params["drawData"].nodes(json).filter(function(d) {
	    return (d.dx > pixcelLimit);
	});
	vis = vis.append("svg:g")
	    .attr("id", "container")
	    .attr("transform", this.params["transform"]);
	this.renderPre();
	var diagram = vis.data([json]).selectAll(this.params["svgItem"])
	    .data(nodes)
	    .enter().append(this.params["svgItem"]);
	diagram.call(this.render,this.params);
    diagram.call(this.commonAttr);
	};
DrawLayout.prototype.renderPre = function(){};
DrawLayout.prototype.render = function(){};
DrawLayout.prototype.commonAttr = function(){
	this.attr("fill-rule", "evenodd")
	    .style("fill", color)
	    .style("stroke", "#fff")
	    .on('click', click)
	    .call(apply_mouseover);	
};

function Sunburst() {};
Sunburst.prototype = Object.create(DrawLayout.prototype);
Sunburst.prototype.get_render_params = function(){
		  var radius = Math.min(SVG_DIMS.width,SVG_DIMS.height) / 2;
		  var partition = d3.layout.partition()
		      .size([2 * Math.PI, radius * radius])
		      .value(function(d) { return d.size; });
		  // By default D3 makes the y size proportional to some area,
		  // so y is a transformation from ~area to a linear scale
		  // so that all arcs have the same radial size.
		  var yScale = d3.scale.linear().domain([0, radius*radius]).range([0, radius]);
		  var arc = d3.svg.arc()
		      .startAngle(function(d) {
		        return Math.max(0, Math.min(2 * Math.PI, d.x));
		      })
		      .endAngle(function(d) {
		        return Math.max(0, Math.min(2 * Math.PI, d.x + d.dx));
		      })
		      .innerRadius(function(d) { return yScale(d.y); })
		      .outerRadius(function(d) { return yScale(d.y + d.dy); });
		  this.params=  {
		    "radius": radius,
		    "transform": "translate(" + SVG_DIMS.width/2 + "," + radius + ")",
		    "minPixel":0.005, // 0.005 radians = 0.29 degrees.
		    "drawData": partition,
		    "svgItem": "path",
		    "arc": arc
		  };
		};
Sunburst.prototype.renderPre = function(){
	// Bounding circle for the sunburst
	vis.append("circle")
    .attr("r", this.params["radius"])
    .style("opacity", 0);
};
Sunburst.prototype.render = function(selection,params){
	selection.attr("id", function(d, i) { return "path-" + i; })
		.attr("d", params["arc"]);	
};

function Icicle(){}
Icicle.prototype = Object.create(DrawLayout.prototype);
Icicle.prototype.get_render_params =  function(){
	var partition = d3.layout.partition()
		.size([SVG_DIMS.width, SVG_DIMS.height])
		.value(function(d) { return d.size; });
	this.params= {
		"minPixel":0.5, // half pixcel width
		"svgItem": "rect",
		"drawData": partition
	};
};
Icicle.prototype.render = function(selection,params){
     this.attr("id", function(d, i) { return "path-" + i; })
	     .attr("x", function(d) { return d.x; })
	     .attr("y", function(d) { return d.y; })
	     .attr("width", function(d) { return d.dx; })
	     .attr("height", function(d) { return d.dy; });	
};

// Colors.
var scale = d3.scale.category20c();

// should make it so that a given function is always the same color
var color = function(d) {
  return scale(d.name);
};

var make_vis_obj = function() {
	return d3.select("#chart")
		.style('margin-left', (DIMS["leftMargin"]+DIMS["widthInfo"])+"px")
		.style('margin-right', 'auto')
		.style('margin-top', DIMS["topMargin"]+"px")
		.append("svg:svg")
		.attr("width", SVG_DIMS.width)
		.attr("height", SVG_DIMS.height);
};

var get_style_value = function(){
	return $(STYLE_SELECT).val();
};


var select_current_style = function(){
	style = get_style_value();
	if (style in LAYOUT_DICTIONARY) {
		var currentLayout = new LAYOUT_DICTIONARY[style];
	}
	else{
		throw new Error("Unknown rendering style '" + style + "'.");
	};
	layout = new DrawStratergy(currentLayout);
	return layout;
};

var vis = make_vis_obj();

var reset_vis = function() {
  // Remove the current figure
  d3.select('svg').remove();
  // Make and draw the new svg container
  vis = make_vis_obj();
};


var clear_and_redraw_vis = function(json) {
  layout = select_current_style();
  reset_vis();
  layout.draw(json);
  d3.select('#container')
    .on('mouseenter', sv_show_info_div)
    .on('mouseleave', sv_hide_info_div);
};



// This is the function that runs whenever the user clicks on an SVG
// element to trigger zooming.
var click = function(d) {
  // check whether we need to do anything
  // (e.g. that the user hasn't clicked on the original root node)
  if (d.name === sv_root_func_name) {
    return;
  }
  var stack_last = _.last(sv_call_stack);
  if (d.name === stack_last) {
    // need to go up a level in the call stack
    sv_call_stack.pop();
    var new_root = _.last(sv_call_stack);
  } else {
    var new_root = d.name;

    // need to construct a new call stack
    // go up the tree until we hit the tip of the call stack
    var this_node = d;
    var local_stack = [new_root];
    while (this_node.parent != null) {
      if (this_node.parent.name === stack_last) {
        // extend the call stack with what we've accumulated
        local_stack.reverse();
        sv_call_stack = sv_call_stack.concat(local_stack);
        break;
      } else {
        local_stack.push(this_node.parent.name);
        this_node = this_node.parent;
      }
    }
  }

  //figure out the new parent name
  if (sv_call_stack.length === 1) {
    var new_parent_name = null;
  } else {
    var new_parent_name = _.first(_.last(sv_call_stack, 2));
  }

  // Create new JSON for drawing a vis from a new root
  sv_draw_vis(new_root, new_parent_name);
  sv_update_call_stack_list();

  // Activate the reset button if we aren't already at the root node
  // And deactivate it if this is the root node
  if (new_root !== sv_root_func_name) {
    d3.select('#resetbutton').node().removeAttribute('disabled');
  } else {
    d3.select('#resetbutton').property('disabled', 'True');
  }
};

var sv_info_template = _.template(
  ['<div class="sv-info-label">Name:</div>',
   '<div class="sv-info-item"><%- name %></div>',
   '<div class="sv-info-label">Cumulative Time:</div>',
   '<div class="sv-info-item"><%= cumulative %> s (<%= cumulative_percent %> %)</div>',
   '<div class="sv-info-label">File:</div>',
   '<div class="sv-info-item"><%- file %></div>',
   '<div class="sv-info-label">Line:</div>',
   '<div class="sv-info-item"><%= line %></div>',
   '<div class="sv-info-label">Directory:</div>',
   '<div class="sv-info-item"><%- directory %></div>'
  ].join('\n'));

var sv_update_info_div = function(d) {
  var re = /^(.*):(\d+)\((.*)\)$/;
  var result = re.exec(d.name);
  var file = result[1];
  var directory = '';
  var slash = Math.max(file.lastIndexOf('/'),file.lastIndexOf('\\'));
  if (slash !== -1) {
    directory = file.slice(0, slash + 1);
    file = file.slice(slash + 1);
  }
  var info = {
    'file': file,
    'directory': directory,
    'line': result[2],
    'name': result[3],
    'cumulative': d.cumulative.toPrecision(3),
    'cumulative_percent': (d.cumulative / sv_total_time * 100).toFixed(2)
  };

  var style = get_style_value();
  var div = $('#sv-info-div');
  div.html(sv_info_template(info));
  // should this be a static width in which case we dont need to change the class types
  if (!div.hasClass(style)){
	  div
	  .removeClass()
	  .addClass(style)
	  .width(DIMS["widthInfo"]);
  }
};


var apply_mouseover = function(selection) {
  selection.on('mouseover', function (d, i) {
    // select all the nodes that represent this exact function
    // and highlight them by darkening their color
    var thisname = d.name;
    var thispath = selection.filter(function(d, i) {
        return d.name === thisname;});
    var thiscolor = d3.rgb('#ff00ff');
    thispath.style('fill', thiscolor.toString());
    sv_update_info_div(d);
    sv_show_info_div();
  })
  .on('mouseout', function(d, i){
      // reset nodes to their original color
      var thisname = d.name;
      var thispath = selection.filter(function(d, i) {
          return d.name === thisname;});
      thispath.style('fill', color(d));
  });
};


// Reset the visualization to its original state starting from the
// main root function.
var resetVis = function() {
  sv_draw_vis(sv_root_func_name);

  // Reset the call stack
  sv_call_stack = [sv_root_func_name];
  sv_update_call_stack_list();

  d3.select('#resetbutton').property('disabled', 'True');
};
d3.select('#resetbutton').on('click', resetVis);


// The handler for when the user changes the depth selection dropdown.
var sv_selects_changed = function() {
  sv_cycle_worker();
  var parent_name = null;
  if (sv_call_stack.length > 1) {
    parent_name = sv_call_stack[sv_call_stack.length - 2];
  }
  sv_hide_error_msg();
  sv_draw_vis(_.last(sv_call_stack), parent_name);
};
d3.select(STYLE_SELECT).on('change', sv_selects_changed);
d3.select(DEPTH_SELECT).on('change', sv_selects_changed);
d3.select(CUTOFF_SELECT).on('change', sv_selects_changed);
