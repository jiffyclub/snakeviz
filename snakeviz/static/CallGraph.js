//Much of this is based on D3s other hierarchical graphs.

callGraphLayout = function(){

  var hierarchy = d3.layout.hierarchy(),
  size = [1, 1]; // width, height

  function position(node, x, dx, dy,level) {
    levelPos[level] = Math.max(...levelPos);
    var children = node.children;
    node.x = dx * levelPos[level];
    node.y = node.depth * dy;
    node.dx = dx;
    node.dy = dy-dy*.4;
    // all lines point down from p1 on the parent to p2 on the child
    node.childLinkX = node.x + node.dx/2;
    node.childLinkY = node.y;
    node.selfParentX = node.x + node.dx/2;
    node.selfParentY = node.y + node.dy;
    if(node.parent){
      node.parentLinkX = node.parent.selfParentX;
      node.parentLinkY = node.parent.selfParentY;
    }
    if (children && (n = children.length)) {
      var i = -1,
      n,
      c;
      while (++i < n) {
        c = children[i];
        if (node.name != c.name){
          position(c, x, dx, dy,level+1);
        }else{
          //remove any previous positional reference to the object
          position(c, null, null, null,null);
        };
      };
    }
    levelPos[level] += 1;
  }

  function changeLinkage(node, replacer){
    node.childLinkX = replacer.childLinkX
    node.childLinkY = replacer.childLinkY
    node.dx = 0.01;
    node.dy = 0.01;
    if (node.children){
      node.children.forEach(function(child){
        replacer.children.forEach(function(newChild){
          if (child.name === newChild.name){
            child.parentLinkX = null
            child.parentLinkY = null
          }
        })
      })
    
    }
  }

  function compare(a,b){
    if (a.depth>b.depth){
      return -1
    }else if (a.depth<b.depth){
      return 1
    }else{
      return 0
    };
  };

  function cullDuplicates(nodes){
    nodeList = []
    for (var node of nodes){
      nodeList.push({depth:node.depth, name:node.name, node:node})
    }
    sortedNodeList = nodeList.sort(compare);
    var usedList={}
    sortedNodeList.forEach(function(node){
      var currentNode = node.node
      if (node.name in usedList &&  node.name !== currentNode.parent.name){
        changeLinkage(currentNode, usedList[node.name])
      }else if ('parent' in currentNode && node.name !== currentNode.parent.name){
        usedList[node.name] = currentNode
      }
    });
  };

  function depth(node) {
    var children = node.children,
    d = 0;
    if (children && (n = children.length)) {
      var i = -1,
      n;
      while (++i < n) d = Math.max(d, depth(children[i]));
    }
    return 1 + d;
  }

  function height(node) {
    var children = node.children,
    h = 1;
    if (children && (n = children.length)) {
      var i = -1,
      h = 0,
      n;
      while (++i < n) h += height(children[i]);
      h = Math.max(1,h-1);
    }
    return h;
  }

  function partition(d, i) {
    var nodes = hierarchy.call(this, d, i);
    depthTree = depth(nodes[0]);
    heightTree = height(nodes[0]);
    levelPos = new Array(depthTree).fill(0);
    position(nodes[0], 0, size[1]/ heightTree, size[0] / depthTree,0);
    cullDuplicates(nodes)
    return nodes;
  }

  partition.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return partition;
  };

  return d3_layout_hierarchyRebind(partition, hierarchy);
};


//A method assignment helper for hierarchy subclasses.
function d3_layout_hierarchyRebind(object, hierarchy) {
  d3.rebind(object, hierarchy, "sort", "children", "value");

  // Add an alias for nodes and links, for convenience.
  object.nodes = object;
  object.links = d3_layout_hierarchyLinks;

  return object;
}

//Returns an array source+target objects for the specified nodes.
function d3_layout_hierarchyLinks(nodes) {
  return d3.merge(nodes.map(function(parent) {
    return (parent.children || []).map(function(child) {
      return {source: parent, target: child};
    });
  }));
}