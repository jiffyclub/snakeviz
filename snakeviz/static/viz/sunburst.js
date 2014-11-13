// This contains the code that renders and controls
// the sunburst visualization.

// Copied, then modified, from http://www.jasondavies.com/coffee-wheel/

var width = 0.8 * Math.min(window.innerHeight, window.innerWidth),
    height = width,
    radius = width / 2,
    x = d3.scale.linear().range([0, 2 * Math.PI]),
    y = d3.scale.pow().exponent(1).domain([0, 1]).range([0, radius]),
    scale = d3.scale.category20c(),   // colors
    duration = 1000;                  // length of animations

var color = function color(d) {
  return scale(d.name);
};

var vis = d3.select("#chart")
    .style('margin-left', 'auto')
    .style('margin-right', 'auto')
    .append("svg:svg")
    .attr("width", width)
    .attr("height", height)
    .append("svg:g")
    .attr("id", "container")
    .attr("transform", "translate(" + radius + "," + radius + ")");

var partition = d3.layout.partition()
    .size([2 * Math.PI, radius * radius])
    .value(function(d) { return d.size; });

var arc = d3.svg.arc()
    .startAngle(function(d) { return d.x; })
    .endAngle(function(d) { return d.x + d.dx; })
    .innerRadius(function(d) { return Math.sqrt(d.y); })
    .outerRadius(function(d) { return Math.sqrt(d.y + d.dy); });

var drawSunburst = function drawSunburst(json) {
  sunburstJSON = json;
  // remove loading bar
  var path = vis.data([json]).selectAll("path").data(partition.nodes);
  path.enter().append("path")
      .attr("id", function(d, i) { return "path-" + i; })
      .attr("d", arc)
      .attr("fill-rule", "evenodd")
      .style("fill", color)
      .style("stroke", "#fff")
      // .on("click", click)
      .call(d3helpertooltip(tooltipText));

  function click(d) {
    path.transition()
      .duration(duration)
      .attrTween("d", arcTween(d));
    // Activate the reset button if we aren't already at the root node
    // And deactivate it if this is the root node
    if (d.depth != 0) {
      d3.select('#resetbutton').node().removeAttribute('disabled');
    } else {
      d3.select('#resetbutton').property('disabled', 'True');
    }
  }
};

var JSONErrorCallback = function JSONCallback() {
  //remove reset button, loading bar, and svg
  d3.select('#resetbutton').remove();
  d3.select('#loadingdiv').remove();
  d3.select('#sunburstsvg').remove();

  // add error div
  var errdiv = d3.select('#chart').append('div')
                 .attr('id', 'jsonerrordiv')
                 .classed('alert', true)
                 .classed('alert-error', true)
                 .classed('alert-block', true)
                 .style('margin-top', '20px');

  // add the close button
  errdiv.append('button')
    .attr('type', 'button')
    .attr('data-dismiss', 'alert')
    .classed('close', true)
    .html('<i class="icon-remove"></i>');

  // add a heading to the error
  errdiv.append('h4')
    .classed('alert-heading', true)
    .html('Error Loading Profile');

  // add friendly text to the error message
  errdiv.append('p')
    .html('<br>Sorry, we were not able to load this profile! ' +
          'You can try profiling a smaller portion of your code. ' +
          'The statistics table below might help you narrow down ' +
          'which portion of your code to focus on.');
};

var JSONCallback = function JSONCallback(json) {
  if (json) {
    drawSunburst(json);
  } else {
    JSONErrorCallback();
  }
};
// d3.json(profile_json_path, JSONCallback);

var resetViz = function resetViz() {
  var path = vis.selectAll("path");
  path.transition()
      .duration(duration)
      .attrTween("d", arcTween(sunburstJSON));
  d3.select('#resetbutton').property('disabled', 'True');
};
d3.select('#resetbutton').on('click', resetViz);

var tooltipText = function tooltipText(d, i) {
  return d.name + ' [' + d.cumulative.toPrecision(3) + 's]';
};

// Interpolate the scales!
function arcTween(d) {
  var my = maxY(d),
      xd = d3.interpolate(x.domain(), [d.x, d.x + d.dx]),
      yd = d3.interpolate(y.domain(), [d.y, my]),
      yr = d3.interpolate(y.range(), [d.y ? 20 : 0, r]);
  return function(d) {
    return function(t) { x.domain(xd(t)); y.domain(yd(t)).range(yr(t)); return arc(d); };
  };
}

function maxY(d) {
  return d.children ? Math.max.apply(Math, d.children.map(maxY)) : d.y + d.dy;
}
