// This contains the code that renders and controls the visualization.

var get_sunburst_render_params = function get_sunburst_render_params() {
  // 80% of the smallest window dimension
  var width = 0.8 * Math.min(window.innerHeight, window.innerWidth);
  var height = width;
  var radius = width / 2;
  var partition = d3.layout.partition()
      .size([2 * Math.PI, radius * radius])
      .value(function(d) { return d.time; });
  // By default D3 makes the y size proportional to some area,
  // so y is a transformation from ~area to a linear scale
  // so that all arcs have the same radial size.
  var y = d3.scale.linear().domain([0, radius * radius]).range([0, radius]);
  var arc = d3.svg.arc()
      .startAngle(function(d) {
        return Math.max(0, Math.min(2 * Math.PI, d.x));
      })
      .endAngle(function(d) {
        return Math.max(0, Math.min(2 * Math.PI, d.x + d.dx));
      })
      .innerRadius(function(d) { return y(d.y); })
      .outerRadius(function(d) { return y(d.y + d.dy); });
  return {
    "width": width,
    "height": height,
    "radius": radius,
    "transform": "translate(" + radius + "," + radius + ")",
    "partition": partition,
    "arc": arc
  };
};

var get_icicle_render_params = function get_icicle_render_params() {
  var width = window.innerWidth * 0.75;
  var height = window.innerHeight * 0.8;
  var leftMargin = 90;
  var topMargin = 60;
  var partition = d3.layout.partition()
      .size([width - leftMargin, height - topMargin])
      .value(function(d) { return d.time; });
  return {
    "width": width,
    "height": height,
    "leftMargin": leftMargin,
    "topMargin": topMargin,
    "transform": "translate(" + leftMargin + "," + topMargin + ")",
    "partition": partition
  };
};

var get_render_params = function get_render_params(style) {
  if (style === "sunburst") {
    return get_sunburst_render_params();
  } else if (style === "icicle") {
    return get_icicle_render_params();
  } else {
    throw new Error("Unknown rendering style '" + style + "'.");
  }
};

// Colors.
var scale = d3.scale.category20c();

// should make it so that a given function is always the same color
var color = function color(d) {
  return scale(d.name);
};


var make_vis_obj = function make_vis_obj (style) {
  var params = get_render_params(style);
  return d3.select("#chart")
    .style('margin-left', 'auto')
    .style('margin-right', 'auto')
    .append("svg:svg")
    .attr("width", params["width"])
    .attr("height", params["height"])
    .append("svg:g")
    .attr("id", "container")
    .attr("transform", params["transform"]);
};
var vis = make_vis_obj("sunburst");


var reset_vis = function reset_vis (style) {
  // Remove the current figure
  d3.select('svg').remove();

  // Make and draw the new svg container
  vis = make_vis_obj(style);
};

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
    $('#resetbutton-zoom').prop('disabled', false);
  } else {
    $('#resetbutton-zoom').prop('disabled', true);
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

  var style = $('#sv-style-select').val();
  var div = $('#sv-info-div');
  div.html(sv_info_tpl(info));

  var radius = get_sunburst_render_params()["radius"];
  if ((style === "sunburst") & (!div.hasClass('sunburst'))) {
    div
      .addClass('sunburst')
      .removeClass('icicle')
      .height(radius * 1.5)
      .width(($('body').width() - (2 * radius)) / 2.1);
  } else if ((style === "icicle") & (!div.hasClass('icicle'))) {
    div
      .addClass('icicle')
      .removeClass('sunburst')
      .height(radius * 1.5)
      .width(200);
  }
};


var apply_mouseover = function apply_mouseover (selection) {
  selection.on('mouseover', function (d, i) {
    // select all the nodes that represent this exact function
    // and highlight them by darkening their color
    var thisname = d.name;
    var thispath = selection.filter(function(d, i) {
        return d.name === thisname;
    });
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


// This is having D3 do its thing.
var drawSunburst = function drawSunburst(json) {
  var params = get_render_params("sunburst");

  // For efficiency, filter nodes to keep only those large enough to see.
  var nodes = params["partition"].nodes(json).filter(function(d) {
    return (d.dx > 0.005); // 0.005 radians = 0.29 degrees.
  });

  // Bounding circle underneath the sunburst, to make it easier to detect
  // when the mouse leaves the parent g.
  vis.append("svg:circle")
    .attr("r", params["radius"])
    .style("opacity", 0);

  var path = vis.data([json]).selectAll("path")
    .data(nodes)
    .enter().append("svg:path")
    .attr("id", function(d, i) { return "path-" + i; })
    .attr("d", params["arc"])
    .attr("fill-rule", "evenodd")
    .style("fill", color)
    .style("stroke", "#fff")
    .on('click', click)
    .call(apply_mouseover);
};

var drawIcicle = function drawIcicle(json) {
  params = get_render_params("icicle");
  var nodes = params["partition"].nodes(json).filter(function(d) {
    return (d.dx > 0.5); // at least half-a-pixel wide to be visible.
  });
  var x = d3.scale.linear()
      .domain([0, nodes[0].dx])
      .range([0, params["width"] - params["leftMargin"]]);
  var y = d3.scale.linear()
      .domain([0, nodes[0].dy * $('#sv-depth-select').val()])
      .range([0, params["height"] - params["topMargin"]]);

  var rect = vis.data([json]).selectAll("rect")
      .data(nodes)
      .enter().append("rect")
      .attr("id", function(d, i) { return "path-" + i; })
      .attr("x", function(d) { return x(d.x); })
      .attr("y", function(d) { return y(d.y); })
      .attr("width", function(d) { return x(d.dx); })
      .attr("height", function(d) { return y(d.dy); })
      .attr("fill-rule", "evenodd")
      .attr("fill", color)
      .attr("stroke", "#FFF")
      .on('click', click)
      .call(apply_mouseover);

  var labels = vis.data([json]).selectAll("text")
        .data(nodes)
        .enter().append("text")
        .attr("x", function(d) { return x(d.x + (d.dx / 2.0)); })
        .attr("y", function(d) { return y(d.y + (d.dy / 2.0)); })
        .attr("width", function(d) { return x(d.dx); })
        .attr("height", function(d) { return y(d.dy); })
        .attr("font-family", "sans-serif")
        .attr("font-size", "15px")
        .attr("fill", "black")
        .attr("text-anchor", "middle")
        .attr("pointer-events", "none");

  // Append the function name
  labels.append("tspan")
    .text(function(d) { return d.display_name; })
    .attr("text-anchor", "middle")
    .attr("x", function(d) { return x(d.x + (d.dx / 2.0)); });
  // Append the time
  labels.append("tspan")
    .text(function(d) { return d.cumulative.toPrecision(3) + " s"; })
    .attr("text-anchor", "middle")
    .attr("x", function(d) { return x(d.x + (d.dx / 2.0)); })
    .attr("dy", "1.2em");

  // Remove labels that don't fit
  d3.selectAll("text")
    .each(function(d, a, b) {
      // var text = d3.selectd(this);
      var bbox = this.getBBox();
      if (bbox.width > x(d.dx)) {
        this.remove();
      }
    });
};

// Clear and redraw the visualization
var redraw_vis = function redraw_vis(json) {
  var style = $('#sv-style-select').val();
  reset_vis(style);
  if (style === "sunburst") {
    drawSunburst(json);
  } else if (style === "icicle") {
    drawIcicle(json);
  }
  d3.select('#container')
    .on('mouseenter', sv_show_info_div)
    .on('mouseleave', sv_hide_info_div);
};


// Reset the visualization to its original state starting from the
// main root function.
var resetVis = function resetViz() {
  sv_draw_vis(sv_root_func_name);

  // Reset the call stack
  sv_call_stack = [sv_root_func_name];
  sv_update_call_stack_list();

  $('#resetbutton-zoom').prop('disabled', true);
};
$('#resetbutton-zoom').on('click', resetVis);


var resetRoot = function resetRoot() {
  // originally set in the setup code in viz.html
  sv_root_func_name = sv_root_func_name__cached;
  resetVis();
  $('#resetbutton-root').prop('disabled', true);
};
$('#resetbutton-root').on('click', resetRoot);


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
d3.select('#sv-style-select').on('change', sv_selects_changed);
d3.select('#sv-depth-select').on('change', sv_selects_changed);
d3.select('#sv-cutoff-select').on('change', sv_selects_changed);
