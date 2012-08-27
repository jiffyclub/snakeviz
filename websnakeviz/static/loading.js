// This implements a sort of loading graphic.
// It uses Boostrap's progress bar at 100%, striped and animated
// to indicate that stuff is happening.

var div = d3.select("#chart");

var progdiv = div.append('div')
    .attr('id', 'loadingdiv')
    .style('position', 'absolute')
    .style('top', '50%')
    .style('left', '25%')
    .style('width', '50%')
    .style('align', 'center')
    .classed('progress', true)
    .classed('progress-striped', true)
    .classed('active', true)

var prog = progdiv.append('div')
    .attr('id', 'loadingbar')
    .classed('bar', true)
    .style('width', '100%');
