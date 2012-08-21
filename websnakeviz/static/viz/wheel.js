// Copied from http://www.jasondavies.com/coffee-wheel/
var w = 900,
    h = w,
    r = w / 2,
    x = d3.scale.linear().range([0, 2 * Math.PI]),
    y = d3.scale.pow().exponent(1).domain([0, 1]).range([0, r]),
    p = 0,
    scale = d3.scale.category20c(),
    duration = 1000;

var div = d3.select("#chart");

var vis = div.append("svg")
    .attr("width", w + p * 2)
    .attr("height", h + p * 2)
    .append("g")
    .attr("transform", "translate(" + (r + p) + "," + (r + p) + ")");

var partition = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.size; });

var arc = d3.svg.arc()
    .startAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x))); })
    .endAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x + d.dx))); })
    .innerRadius(function(d) { return Math.max(0, d.y ? y(d.y) : d.y); })
    .outerRadius(function(d) { return Math.max(0, y(d.y + d.dy)); });

function draw_sunburst(json) {
  sunburst_json = json;
  var path = vis.data([json]).selectAll("path").data(partition.nodes);
  path.enter().append("path")
      .attr("id", function(d, i) { return "path-" + i; })
      .attr("d", arc)
      .attr("fill-rule", "evenodd")
      .style("fill", color)
      .style("stroke", "#fff")
      .on("click", click)
      .call(d3helpertooltip(tooltip_text));

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
    };
  }
}
d3.json('/json/' + profile_name + '.json', draw_sunburst);

function reset_viz() {
  var path = vis.selectAll("path");
  path.transition()
      .duration(duration)
      .attrTween("d", arcTween(sunburst_json));
  d3.select('#resetbutton').property('disabled', 'True');
}
d3.select('#resetbutton').on('click', reset_viz);

function isParentOf(p, c) {
  if (p === c) return true;
  if (p.children) {
    return p.children.some(function(d) {
      return isParentOf(d, c);
    });
  }
  return false;
}

function color(d) {
  return scale(d.name + d.filename + d.directory + d.line_number);
}

function tooltip_text(d, i) {
  return d.name + '@' + d.filename + ':' + d.line_number + ' [' +
         d.cummulative.toPrecision(3) + 's]';
}

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
