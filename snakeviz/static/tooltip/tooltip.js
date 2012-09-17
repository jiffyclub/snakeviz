// This file contains the code for the tooltip and node highlighting
// that occurs when users mouse over the visualization.

// This function positions the tooltip to the right or the left of the
// mouse depending whether the mouse is on the left or right half of the
// window, respectively. This prevents the tooltip from running into the
// edge of the window.
var tooltipPosition = function tooltipPosition(mousePos, tooltipDiv) {
    var w = window.innerWidth,
        mx = mousePos[0],
        my = mousePos[1];

    tooltipDiv.style('top', (my - 15) + 'px');

    if (mx < w / 2) {
        // tooltip on the right
        tooltipDiv.style('right', null);
        tooltipDiv.style('left', (mx + 10) + 'px');
    } else {
        // tooltip on the left
        tooltipDiv.style('left', null);
        tooltipDiv.style('right', (w - mx - 10) + 'px');
    };
}

d3helpertooltip = function d3helpertooltip(accessor) {
    return function(selection) {
        var tooltipDiv;
        var bodyNode = d3.select('body').node();

        selection.on("mouseover", function(d, i) {
            // Clean up lost tooltips
            d3.select('body').selectAll('div.tooltip').remove();

            // Append tooltip
            tooltipDiv = d3.select('body').append('div').attr('class', 'viztooltip');
            tooltipDiv.style('position', 'absolute')
                .style('z-index', 1001);

            var absoluteMousePos = d3.mouse(bodyNode);
            tooltipPosition(absoluteMousePos, tooltipDiv);

            // Add text using the accessor function
            var tooltipText = accessor(d, i) || '';

            // Crop text arbitrarily
            tooltipDiv.style('width', function(d, i) {
                return (tooltipText.length > 80) ? '300px' : null;
            })
                .text(tooltipText);

            // select all the nodes that represent this exact function
            // and highlight them by darkening their color
            var thisname = d.name;
            var thisfilename = d.filename;
            var thisdirectory = d.directory;
            var thislinenumber = d.line_number;
            var thispath = selection.filter(function(d, i) {
                return d.name == thisname &
                       d.filename == thisfilename &
                       d.directory == thisdirectory &
                       d.line_number == thislinenumber;})
            var thiscolor = d3.rgb('#ff00ff');
            thispath.style('fill', thiscolor.toString());
        })
        .on('mousemove', function(d, i) {
            // Move tooltip
            var absoluteMousePos = d3.mouse(bodyNode);
            tooltipPosition(absoluteMousePos, tooltipDiv);
            var tooltipText = accessor(d, i) || '';
            tooltipDiv.text(tooltipText);
        })
        .on("mouseout", function(d, i){
            // Remove tooltip
            tooltipDiv.remove();

            // reset nodes to their original color
            var thisname = d.name;
            var thisfilename = d.filename;
            var thisdirectory = d.directory;
            var thislinenumber = d.line_number;
            var thispath = selection.filter(function(d, i) {
                return d.name == thisname &
                       d.filename == thisfilename &
                       d.directory == thisdirectory &
                       d.line_number == thislinenumber;})
            thispath.style('fill', color(d))
        });

    };
};
