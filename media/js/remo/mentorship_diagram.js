function get_reps(users) {

    var mentorship = {};
    var original_council = [];

    users.forEach(function(value, index, array) {
        var rep = {'user_id': value.resource_uri.split('/')[4],
                   'name': value.fullname,
                   'url': value.profile.profile_url,
                   'mentor': value.profile.mentor.split('/')[4]};

        if (rep.mentor === rep.user_id) {
            delete rep.mentor;
            original_council.push(rep);
        }
        array[index] = rep;
    });

    users.forEach(function(mentor) {
       var mentees = [];
       users.forEach(function(mentee){
           if (mentee.mentor === mentor.user_id) {
               mentees.push(mentee);
           }
       });
       if (mentees.length > 0) {
           mentorship[mentor.user_id] = {'name': mentor.name, 'children': mentees};
       }
    });

    return {'mentorship': mentorship, 'original_council': original_council};
}

function create_tree(tree, nodes) {
    tree.children.forEach(function(value){
        if (nodes[value.user_id]) {
          value.children = nodes[value.user_id].children;
          create_tree(value, nodes);
        }
    });

    return tree;
}

d3.selection.prototype.moveToFront = function() {
    return this.each(function() { this.parentNode.appendChild(this);});
};

function highlight_path(curr_node,i) {
    var focus = d3.event.type === 'mouseover' ? true : false;
    while (curr_node.depth>0) {
      d3.select('#id-' + curr_node.user_id).classed('path', focus);
      d3.select('#node-id-' + curr_node.user_id).classed('focus', focus);
      curr_node = curr_node.parent;
    }
    d3.selectAll('.focus').moveToFront();
}

function create_diagram(obj) {

    var diameter = 960;

    var tree = d3.layout.tree()
        .size([360, 400])
        .separation(function(a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });

    var diagonal = d3.svg.diagonal.radial()
        .projection(function(d) { return [d.y, d.x / 180 * Math.PI]; });

    var svg = d3.select('#mentorship-visualization-container').append('svg')
        .attr('width', diameter)
        .attr('height', diameter)
        .append('g')
        .attr('transform', 'translate(' + diameter / 2 + ',' + diameter / 2 + ')');

    var nodes = tree.nodes(obj),
        links = tree.links(nodes);

    var link = svg.selectAll('.link')
        .data(links)
        .enter().append('path')
        .attr('class', 'link')
        .attr('d', diagonal)
        .attr('id', function(d, i) { return 'id-' + d.target.user_id; });

    var node = svg.selectAll('.node')
        .data(nodes)
        .enter().append('g')
        .attr('class', function(d, i) {return d.children ? 'node' : 'leaf';})
        .attr('id', function(d, i) { return 'node-id-' + d.user_id; })
        .attr('transform', function(d) { return 'rotate(' + (d.x - 90) + ')translate(' + d.y + ')'; })
        .on('mouseover', highlight_path)
        .on('mouseout', highlight_path);

    node.append('circle')
        .attr('r', 4.5)
        .attr('id', function(d, i) { return 'circle-id-' + d.user_id; });

    node.append('a')
        .attr('xlink:href', function(d) { return d.url; })
        .append('text')
        .attr('dy', '.31em')
        .attr('text-anchor', function(d) { return d.x < 180 ? 'start' : 'end'; })
        .attr('transform', function(d) { return d.x < 180 ? 'translate(8)' : 'rotate(180)translate(-8)'; })
        .text(function(d) { return d.name; })
        .attr('id', function(d, i) { return 'text-id-' + d.user_id; });

    d3.select(self.frameElement).style('height', diameter - 150 + 'px');
}

function loader_canvas_icon_init() {
    var sl = new CanvasLoader('profiles-loading');
    sl.setColor('#888888');
    sl.setDiameter(24);
    sl.setDensity(30);
    sl.setRange(0.8);
    sl.setFPS(23);
    sl.show();
}

$(document).ready(function() {
    loader_canvas_icon_init();
    $('#profiles-loading').append('<div>Please wait while viz magic happens!</div>');
    $.ajax({
             type: 'GET',
             url: '/api/v1/rep/?limit=500',
             async: true,
             contentType: 'application/json',
             dataType: 'json',

             success: function(data) {
               var reps = get_reps(data.objects);
               var mentorship_tree = {};
               mentorship_tree.name = 'Original Council';
               mentorship_tree.children = reps.original_council;

               $('#profiles-loading-wrapper').hide();
               create_diagram(create_tree(mentorship_tree, reps.mentorship));
             }
         });
});