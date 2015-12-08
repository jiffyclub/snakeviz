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
	     callgraph: CallGraph,
	};

function DrawLayout() {
	this.params = this.get_render_params();
	this.vis = this.setUp();
};
DrawLayout.prototype.setUp = function(){
	return  d3.select("#chart")
		.style('margin-left', (DIMS["leftMargin"]+DIMS["widthInfo"])+"px")
		.style('margin-right', 'auto')
		.style('margin-top', DIMS["topMargin"]+"px");
};
DrawLayout.prototype.resetVis = function(){
	d3.select('svg').remove();
};
DrawLayout.prototype.get_render_params = function(){};
DrawLayout.prototype.draw = function(json){
	var pixcelLimit = this.params["minPixel"];
	var visibleNodes = this.params["drawData"].nodes(json).filter(function(d) {
	    return (d.dx > pixcelLimit);
	});
	var thisVis = this.addContainer(this.vis);
	this.renderPre(thisVis);
	var diagram = thisVis.data([json]).selectAll(this.params["svgItem"])
	    .data(visibleNodes)
	    .enter();
	var mainDiagram = diagram.append(this.params["svgItem"]);
	mainDiagram.call(this.render,this.params);
	mainDiagram.call(this.commonAttr);
    this.renderPost(diagram);
	};
DrawLayout.prototype.renderPre = function(vis){};
DrawLayout.prototype.render = function(){};
DrawLayout.prototype.renderPost = function(vis){};
DrawLayout.prototype.addContainer = function(vis){
	return vis.append("svg:svg")
		.attr("width", SVG_DIMS.width)
		.attr("height", SVG_DIMS.height)
		.append("g")
	    .attr("id", "container")
	    .attr("transform", this.params["transform"])
	    .on('mouseenter', sv_show_info_div)
        .on('mouseleave', sv_hide_info_div);
};
DrawLayout.prototype.commonAttr = function(){
	this.attr("fill-rule", "evenodd")
	    .style("fill", color)
	    .style("stroke", "#fff")
	    .on('click', click)
	    .call(apply_mouseover);	
};

function Sunburst() {
	DrawLayout.call(this);	
};
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
		  return {
		    "radius": radius,
		    "transform": "translate(" + SVG_DIMS.width/2 + "," + radius + ")",
		    "minPixel":0.005, // 0.005 radians = 0.29 degrees.
		    "drawData": partition,
		    "svgItem": "path",
		    "arc": arc
		  };
		};
Sunburst.prototype.renderPre = function(vis){
	// Bounding circle for the sunburst
	vis.append("circle")
    .attr("r", this.params["radius"])
    .style("opacity", 0);
};
Sunburst.prototype.render = function(selection,params){
	selection.attr("id", function(d, i) { return "path-" + i; })
		.attr("d", params["arc"]);	
};

function Icicle(){
	DrawLayout.call(this);	
}
Icicle.prototype = Object.create(DrawLayout.prototype);
Icicle.prototype.get_render_params =  function(){
	var partition = d3.layout.partition()
		.size([SVG_DIMS.width, SVG_DIMS.height])
		.value(function(d) { return d.size; });
	return {
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

function CallGraph(){
	DrawLayout.call(this);	
}

CallGraph.prototype = Object.create(DrawLayout.prototype);

CallGraph.prototype.get_render_params =  function(){
	var partition = callGraphLayout()
		.size([SVG_DIMS.width, SVG_DIMS.height])
		.value(function(d) { return d.size; });	
	return {
		"minPixel": 0 , // half pixcel width
		"svgItem": "rect",
		"drawData": partition
	};
};

CallGraph.prototype.render = function(selection,params){
     this.attr("id", function(d, i) { return "path-" + i; })
	     .attr("y", function(d) { return d.x; })
	     .attr("x", function(d) { return d.y; })
	     .attr("height", function(d) { return d.dx; })
	     .attr("width", function(d) { return d.dy; });	   
};

CallGraph.prototype.renderPost = function(vis){
	vis.append("line")
	.attr("y1", function(d) { return d.x1; })
	.attr("x1", function(d) { return d.y1; })
	.attr("y2", function(d) { return d.x2; })
	.attr("x2", function(d) { return d.y2; })
	.style("stroke", "rgb(255,0,0)");
};

// Colors.
var scale = d3.scale.category20c();

// should make it so that a given function is always the same color
var color = function(d) {
  return scale(d.name);
};

var get_style_value = function(){
	return $(STYLE_SELECT).val();
};

var select_current_style = function(){
	style = get_style_value();
	if (style in LAYOUT_DICTIONARY) {
		var currentLayout = new LAYOUT_DICTIONARY[style]();
	}
	else{
		throw new Error("Unknown rendering style '" + style + "'.");
	};
	return currentLayout;
};
var masterData = null;

var clear_and_redraw_vis = function(json) {
  layout = select_current_style();
  layout.resetVis();
  layout.draw(json);
  if (masterData === null){
	  masterData =  d3.layout.partition().nodes(json);
  }
};

// This is the function that runs whenever the user clicks on an SVG
// element to trigger zooming.
var click = function(d) {
	highlighter.removeAll();
	sv_draw_vis(d.name,d.parent_name);
};
var findData= function(functionName, parentName){	
	 var matchingData = masterData.filter(function(obj){
		return obj.name===functionName && 
		obj.parent_name === parentName;});
	 if (matchingData.length != 0){
		 matchingData = matchingData[0];
	 }
	 return matchingData;
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
  if (!div.hasClass(style)){
	  div
	  .width(DIMS["widthInfo"]);
  }
};


var apply_mouseover = function(selection) {
	selection.on('mouseover', function (d) {
		// select all the nodes that represent this exact function
		// and highlight them by darkening their color
		var thisName = d.name;
		var thispath = selection.filter(function(d) {
			return d.name === thisName;});
		var thiscolor = d3.rgb('#ff00ff');
		thispath.style('fill', thiscolor.toString());
		sv_update_info_div(d);
		sv_show_info_div();
		highlighter.highlight(sv_item_name(thisName));
  })
  .on('mouseout', function(d){
      // reset nodes to their original color
      highlighter.remove();
      var thisName = d.name;
      var thispath = selection.filter(function(d) {
          return d.name === thisName;});
      thispath.style('fill', color(d));
  });
};

var rowHighlighter = function(tableReference){
	var htmlClassName = 'highlight';
	var table = $(tableReference).DataTable();
	this.highlight = function(rowName){
		var rowToHighlight = table.rows().eq(0).filter( function(rowIdx){
			return htmlToText(table.cell( rowIdx, 5 ).data()) === rowName ? true : false;
			});
		selectRows( rowToHighlight )
		    .addClass( htmlClassName );
		this.highlightedRows = rowToHighlight;
		};
	this.remove = function(){
		unhighlight( this.highlightedRows );
	};
	this.removeAll = function(){
		unhighlight( table.rows );
	};
	unhighlight = function(rows){
		selectRows(rows)
		    .removeClass( htmlClassName );
	};
	selectRows = function(rows){
		return table.rows( rows )
		    .nodes()
		    .to$();
	};
};


lastFunctionName = "";
lastParentNumber = 0;

var tableClick = function(){
	var table = $('#pstats-table').DataTable();
	var rowIdx = table.cell(this).index().row;
	var functionName = htmlToText(table.cell( rowIdx, 6 ).data());
	var parentArray = table.cell( rowIdx, 7 ).data();
	if(lastFunctionName===functionName){
		lastParentNumber+=1;
		if (lastParentNumber===parentArray.length){
			lastParentNumber=0;
		}
	}else{
		lastParentNumber=0;
	};
	parentName = htmlToText(parentArray[lastParentNumber]);
	callStack.resetStack();
	sv_draw_vis(functionName,parentName);
	lastFunctionName = functionName;
};


var htmlToText = function(html){
	return $.parseHTML(html)[0].textContent;
};

// Reset the visualization to its original state starting from the
// main root function.
var resetVis = function() {
  sv_draw_vis(sv_root_func_name);

  // Reset the call stack
  callStack.resetStack();
  callStack.updateDisplay();
  resetButton.disable();
};

var resetButton =  {	
	button : d3.select('#resetbutton'),	
	enable : function(){
		this.button.node().removeAttribute('disabled');
		},
	disable : function(){
		this.button.property('disabled','True');
	},
	setup : function(){
		this.button.on('click', resetVis);
	}
};

resetButton.setup();

// The handler for when the user changes the depth selection dropdown.
var sv_selects_changed = function() {
  sv_cycle_worker();
  sv_hide_error_msg();
  sv_draw_vis(null,null);
};
d3.select(STYLE_SELECT).on('change', sv_selects_changed);
d3.select(DEPTH_SELECT).on('change', sv_selects_changed);
d3.select(CUTOFF_SELECT).on('change', sv_selects_changed);
