$(document).ready(function() {
    'use strict';

    /* Graphs Initialization */
    var margin = {top: 20, right: 50, bottom: 50, left: 50};
    margin.vertical = margin.top + margin.bottom;
    margin.horizontal = margin.left + margin.right;
    var width = 960 - margin.horizontal,
    height = 350 - margin.vertical;

    function weekify(week) {
        var offset = 12 - week;
        var d = new Date();
        d.setDate(d.getDate() - 7*offset);
        var y = d.getFullYear();
        var onejan = new Date(y, 0, 1);
        var w = Math.ceil((((d - onejan) / 86400000) + onejan.getDay() + 1) / 7);
        return y + 'w' + w;
    }

    function people_graph(key, value) {
        var x = d3.scale.linear()
                  .range([0, width]);

        var y = d3.scale.linear()
                  .range([height, 0]);

        var xAxis = d3.svg.axis()
                      .scale(x)
                      .tickFormat(weekify)
                      .orient('bottom');

        var yAxis = d3.svg.axis()
                      .scale(y)
                      .tickFormat(d3.format('d'))
                      .orient('left');

        var area_inactive = d3.svg.area()
                              .x(function(d) { return x(d.week); })
                              .y0(height)
                              .y1(function(d) { return y(d.inactive); });

        var area_active = d3.svg.area()
                                .x(function(d) { return x(d.week); })
                                .y0(height)
                                .y1(function(d) { return y(d.active_stack); });

        var area_casual = d3.svg.area()
                                .x(function(d) { return x(d.week); })
                                .y0(height)
                                .y1(function(d) { return y(d.casual_stack); });

        var area_core = d3.svg.area()
                          .x(function(d) { return x(d.week); })
                          .y0(height)
                          .y1(function(d) { return y(d.core_stack); });

        $('#graph-people').text('');
        var svg = d3.select('#graph-people').append('svg')
                    .attr('width', width + margin.left + margin.right)
                    .attr('height', height + margin.top + margin.bottom)
                    .append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var tip = d3.tip()
                    .attr('class', 'd3-tip')
                    .offset([35, 0])
                    .html(function(d) {
                        return '<strong>Inactive:</strong> <span style="color:red">'
                               + d.inactive + '</span><br>' +
                               '<strong>Active:</strong> <span style="color:red">'
                               + d.active + '</span><br>' +
                               '<strong>Casual:</strong> <span style="color:red">'
                               + d.casual + '</span><br>' +
                               '<strong>Core:</strong> <span style="color:red">'
                               + d.core + '</span><br>' +
                               '<strong>Total:</strong> <span style="color:red">'
                               + d.active_total + '</span>';
                    });

        svg.call(tip);

        var apiurl = '/api/kpi/people/?format=json&'
        if ((typeof(key)!='undefined') && (typeof(value)!='undefined')) {
            apiurl += key + '=' + value;
        }
        d3.json(apiurl, function(error, data) {
            $('#people-total').text(data.total);
            $('#people-total_quarter').text(data.quarter_total);
            $('#people-total_week').text(data.week_total);
            $('#people-percentage_week').text(data.week_growth_percentage);
            $('#people-percentage_quarter').text(data.quarter_growth_percentage);

            var weeks = data.total_per_week;

            weeks.forEach(function(d) {
                d.week = +d.week;
                d.core = +d.core;
                d.active = +d.active;
                d.casual = +d.casual;
                d.inactive = +d.inactive;
                d.active_stack = d.active + d.inactive;
                d.casual_stack = d.casual + d.active_stack;
                d.core_stack = d.core + d.casual_stack;
                d.active_total = d.core + d.active + d.casual + d.inactive;
            });

            var formatPercent = d3.format('%U');

            x.domain([1, d3.max(weeks, function(d) { return d.week; })]);
            y.domain([0, d3.max(weeks, function(d) { return d.active_total; })]);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-people-core')
               .attr('d', area_core);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-people-casual')
               .attr('d', area_casual);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-people-active')
               .attr('d', area_active);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-people-inactive')
               .attr('d', area_inactive);

            svg.append('g')
               .attr('class', 'x axis')
               .attr('transform', 'translate(0,' + height + ')')
               .call(xAxis);

            svg.append('g')
               .attr('class', 'y axis')
               .call(yAxis)
               .append('text');

            svg.append('text')
               .attr('transform', 'rotate(-90)')
               .attr('y', -50)
               .attr('x', -40 - (height / 2))
               .attr('dy','1em')
               .attr('class', 'axis-label')
               .text('Number of Reps');

            svg.append('text')
               .attr('x', (width / 2) - 40)
               .attr('y', height + 40)
               .attr('text-anchor', 'middle')
               .attr('class', 'axis-label')
               .text('Weeks');

            var width_block = width / (weeks.length - 1);

            svg.selectAll('.area-people')
               .data(weeks)
               .enter()
               .append('rect')
               .attr('class', 'info-area')
               .attr('x', function (d) { return ((d.week - 1) * width_block - 20) })
               .attr('y', function (d) { return 0; })
               .attr('height', function (d) { return height; })
               .attr('width', '40px')
               .on('mouseover', function (d, i) {
                   tip.show(d);
                   d3.select(this).style('opacity', 0.2);
               })
               .on('mouseout', function (d, i) {
                   tip.hide(d);
                   d3.select(this).style('opacity', 0);
               });
        });
    }

    function events_graph(key, value) {
        var x = d3.scale.linear()
                  .range([0, width]);

        var y = d3.scale.linear()
                  .range([height, 0]);

        var xAxis = d3.svg.axis()
                      .scale(x)
                      .tickFormat(weekify)
                      .orient('bottom');

        var yAxis = d3.svg.axis()
                      .scale(y)
                      .tickFormat(d3.format('d'))
                      .orient('left');

        var area = d3.svg.area()
                     .x(function(d) { return x(d.week); })
                     .y0(height)
                     .y1(function(d) { return y(d.events); });

        $('#graph-events').text('');
        var svg = d3.select('#graph-events').append('svg')
                    .attr('width', width + margin.left + margin.right)
                    .attr('height', height + margin.top + margin.bottom)
                    .append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var tip = d3.tip()
                    .attr('class', 'd3-tip')
                    .offset([0, 0])
                    .html(function(d) {
                        return '<strong>Events:</strong> <span style="color:red">' + d.events + '</span>';
                    });

        svg.call(tip);

        var apiurl = '/api/kpi/events/?format=json&'
        if ((typeof(key)!='undefined') && (typeof(value)!='undefined')) {
            apiurl += key + '=' + value;
        }
        d3.json(apiurl, function(error, data) {
            $('#events-total').text(data.total);
            $('#events-total_quarter').text(data.quarter_total);
            $('#events-total_week').text(data.week_total);
            $('#events-percentage_week').text(data.week_growth_percentage);
            $('#events-percentage_quarter').text(data.quarter_growth_percentage);

            var weeks = data.total_per_week;

            weeks.forEach(function(d) {
                d.week = +d.week;
                d.events = +d.events;
            });

            var formatPercent = d3.format('%U');

            x.domain([1, d3.max(weeks, function(d) { return d.week; })]);
            y.domain([0, d3.max(weeks, function(d) { return d.events; })]);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-events')
               .attr('d', area);

            svg.append('g')
               .attr('class', 'x axis')
               .attr('transform', 'translate(0,' + height + ')')
               .call(xAxis);

            svg.append('g')
               .attr('class', 'y axis')
               .call(yAxis)
               .append('text');

            svg.append('text')
               .attr('transform', 'rotate(-90)')
               .attr('y', -50)
               .attr('x', -40 - (height / 2))
               .attr('dy','1em')
               .attr('class', 'axis-label')
               .text('Number of Events');

            svg.append('text')
               .attr('x', (width / 2) - 40)
               .attr('y', height + 40)
               .attr('text-anchor', 'middle')
               .attr('class', 'axis-label')
               .text('Weeks');

            var width_block = width / (weeks.length - 1);

            svg.selectAll('.line-events')
               .data(weeks)
               .enter()
               .append('rect')
               .attr('class', 'info-area')
               .attr('id', function (d) { return 'w' + d.week; })
               .attr('x', function (d) { return ((d.week - 1) * width_block - 20) })
               .attr('y', function (d) { return 0; })
               .attr('height', function (d) { return height; })
               .attr('width', '40px')
               .on('mouseover', function (d, i) {
                   tip.show(d);
                   d3.select(this).style('opacity', 0.2);
               })
               .on('mouseout', function (d, i) {
                   tip.hide(d);
                   d3.select(this).style('opacity', 0);
               });
        });
    }

    function activities_graph(key, value) {
        var x = d3.scale.linear()
                  .range([0, width]);

        var y = d3.scale.linear()
                  .range([height, 0]);

        var xAxis = d3.svg.axis()
                      .scale(x)
                      .tickFormat(weekify)
                      .orient('bottom');

        var yAxis = d3.svg.axis()
                      .scale(y)
                      .tickFormat(d3.format('d'))
                      .orient('left');

        var area = d3.svg.area()
                     .x(function(d) { return x(d.week); })
                     .y0(height)
                     .y1(function(d) { return y(d.activities); });

        $('#graph-activities').text('');
        var svg = d3.select('#graph-activities').append('svg')
                    .attr('width', width + margin.left + margin.right)
                    .attr('height', height + margin.top + margin.bottom)
                    .append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var tip = d3.tip()
                    .attr('class', 'd3-tip')
                    .offset([35, 0])
                    .html(function(d) {
                        return '<strong>Activities:</strong> <span style="color:red">' + d.activities + '</span>';
                    });

        svg.call(tip);

        var apiurl = '/api/kpi/activities/?format=json&'
        if ((typeof(key)!='undefined') && (typeof(value)!='undefined')) {
            apiurl += key + '=' + value;
        }
        d3.json(apiurl, function(error, data) {
            $('#activities-total').text(data.total);
            $('#activities-total_quarter').text(data.quarter_total);
            $('#activities-total_week').text(data.week_total);
            $('#activities-percentage_week').text(data.week_growth_percentage);
            $('#activities-percentage_quarter').text(data.quarter_growth_percentage);

            var weeks = data.total_per_week;

            weeks.forEach(function(d) {
                d.week = +d.week;
                d.activities = +d.activities;
            });

            var formatPercent = d3.format('%U');

            x.domain([1, d3.max(weeks, function(d) { return d.week; })]);
            y.domain([0, d3.max(weeks, function(d) { return d.activities; })]);

            svg.append('path')
               .datum(weeks)
               .attr('class', 'area-activities')
               .attr('d', area);

            svg.append('g')
               .attr('class', 'x axis')
               .attr('transform', 'translate(0,' + height + ')')
               .call(xAxis);

            svg.append('g')
               .attr('class', 'y axis')
               .call(yAxis);

            svg.append('text')
               .attr('transform', 'rotate(-90)')
               .attr('y', -50)
               .attr('x', -40 - (height / 2))
               .attr('dy','1em')
               .attr('class', 'axis-label')
               .text('Number of Activities');

            svg.append('text')
               .attr('x', (width / 2) - 40)
               .attr('y', height + 40)
               .attr('text-anchor', 'middle')
               .attr('class', 'axis-label')
               .text('Weeks');

            var width_block = width / (weeks.length - 1);

            svg.selectAll('.line-activities')
               .data(weeks)
               .enter()
               .append('rect')
               .attr('class', 'info-area')
               .attr('x', function (d) { return ((d.week - 1) * width_block - 20) })
               .attr('y', function (d) { return 0; })
               .attr('height', function (d) { return height; })
               .attr('width', '40px')
               .on('mouseover', function (d, i) {
                   tip.show(d);
                   d3.select(this).style('opacity', 0.2);
               })
               .on('mouseout', function (d, i) {
                   tip.hide(d);
                   d3.select(this).style('opacity', 0);
               });
        });
    }

    /* Draw all graphs */
    people_graph();
    events_graph();
    activities_graph();

    /* Filtering */
    $('select').change(function() {
        $('.d3-graph').html('<div class="three-quarters">loading...</div>');
        var currentId = $(this).attr('id');
        var value = $('#' + currentId + ' option:selected').val();
        var key = $(this).data('query');
        people_graph(key, value);
        events_graph(key, value);
        activities_graph(key, value);
    });
});
