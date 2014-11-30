// This contains the code that renders and controls
// the sunburst visualization.


// 80% of the smallest window dimension
var width = 0.8 * Math.min(window.innerHeight, window.innerWidth),
    height = width,
    radius = width / 2,
    scale = d3.scale.category20c();   // colors


// should make it so that a given function is always the same color
var color = function color(d) {
  return scale(d.name);
};


var make_vis_obj = function make_vis_obj () {
  return d3.select("#chart")
    .style('margin-left', 'auto')
    .style('margin-right', 'auto')
    .append("svg:svg")
    .attr("width", width)
    .attr("height", height)
    .append("svg:g")
    .attr("id", "container")
    .attr("transform", "translate(" + radius + "," + radius + ")");
};
var vis = make_vis_obj();


var reset_vis = function reset_vis () {
  // Remove the current figure
  d3.select('svg').remove();

  // Make and draw the new svg container
  vis = make_vis_obj();
};


var partition = d3.layout.partition()
  .size([2 * Math.PI, radius * radius])
  .value(function(d) { return d.size; });


// By default D3 makes the y size proportional to some area,
// so y is a transformation from ~area to a linear scale
// so that all arcs have the same radial size.
var y = d3.scale.linear().domain([0, radius * radius]).range([0, radius]);
var arc = d3.svg.arc()
  .startAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, d.x)); })
  .endAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, d.x + d.dx)); })
  .innerRadius(function(d) { return y(d.y); })
  .outerRadius(function(d) { return y(d.y + d.dy); });


// This is the function that runs whenever the user clicks on an SVG
// element to trigger zooming.
var click = function click(d) {
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

var sv_info_tpl = _.template(
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

var sv_update_info_div = function sv_update_info_div (d) {
  var re = /^(.*):(\d+)\((.*)\)$/;
  var result = re.exec(d.name);
  var file = result[1];
  var directory = '';
  var slash = file.lastIndexOf('/');
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
  $('#sv-info-div')
    .html(sv_info_tpl(info))
    .height(radius * 1.5)
    .width(($('body').width() - (2 * radius)) / 2.1);
};


var apply_mouseover = function apply_mouseover (selection) {
  selection.on('mouseover', function (d, i) {
    // select all the nodes that represent this exact function
    // and highlight them by darkening their color
    var thisname = d.name;
    var thispath = selection.filter(function(d, i) {
        return d.name === thisname;})
    var thiscolor = d3.rgb('#ff00ff');
    thispath.style('fill', thiscolor.toString());
    sv_update_info_div(d);
  })
  .on('mouseout', function(d, i){
      // reset nodes to their original color
      var thisname = d.name;
      var thispath = selection.filter(function(d, i) {
          return d.name === thisname;});
      thispath.style('fill', color(d));
  });
};


// This is having D3 do its thing.
var drawSunburst = function drawSunburst(json) {
  // Bounding circle underneath the sunburst, to make it easier to detect
  // when the mouse leaves the parent g.
  vis.append("svg:circle")
    .attr("r", radius)
    .style("opacity", 0);

  // For efficiency, filter nodes to keep only those large enough to see.
  var nodes = partition.nodes(json)
    .filter(function(d) {
      return (d.dx > 0.005); // 0.005 radians = 0.29 degrees
    });

  var path = vis.data([json]).selectAll("path")
    .data(nodes)
    .enter().append("svg:path")
    .attr("id", function(d, i) { return "path-" + i; })
    .attr("d", arc)
    .attr("fill-rule", "evenodd")
    .style("fill", color)
    .style("stroke", "#fff")
    .on('click', click)
    .call(apply_mouseover);

  d3.select('#container')
    .on('mouseenter', sv_show_info_div)
    .on('mouseleave', sv_hide_info_div);
};


// Clear and redraw the visualization
var redraw_vis = function redraw_vis(json) {
  reset_vis();
  drawSunburst(json);
};


// Reset the visualization to its original state starting from the
// main root function.
var resetVis = function resetViz() {
  sv_draw_vis(sv_root_func_name);

  // Reset the call stack
  sv_call_stack = [sv_root_func_name];
  sv_update_call_stack_list();

  d3.select('#resetbutton').property('disabled', 'True');
};
d3.select('#resetbutton').on('click', resetVis);


// The handler for when the user changes the depth selection dropdown.
var sv_selects_changed = function sv_selects_changed() {
  sv_cycle_worker();
  var parent_name = null;
  if (sv_call_stack.length > 1) {
    parent_name = sv_call_stack[sv_call_stack.length - 2];
  }
  sv_hide_error_msg();
  sv_draw_vis(_.last(sv_call_stack), parent_name);
};
d3.select('#sv-depth-select').on('change', sv_selects_changed);
d3.select('#sv-cutoff-select').on('change', sv_selects_changed);
