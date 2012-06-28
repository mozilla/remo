var markers_array = [];
var map;
var request;

function initialize_map() {
    // Initialize map.
    map = new L.Map('map', { minZoom: 1 });
    attribution = ('Map data &copy; <a href="http://openstreetmap.org">' +
                   'OpenStreetMap</a> contributors, <a href="http://creativecommons.org/' +
                   'licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © ' +
                   '<a href="http://cloudmade.com">CloudMade</a>')
    cloudmade = new L.TileLayer('http://{s}.tile.cloudmade.com/' +
                                'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                '997/256/{z}/{x}/{y}.png',
                                { attribution: attribution, maxZoom: 18 });
    center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    map.setView(center, 2).addLayer(cloudmade);

    // When user clicks on map and a search filter exists, remove filter.
    map.on('click', function(e) {
        var val = $('#searchfield').val();
        if (val != '') {
            search_string = '';
            $('#searchfield').val(search_string);
            $('#searchfield').trigger('input');
        }
    });
}


function add_pointers() {
    // Add user pointers on map.
    $('.profiles-li-item').each(function(index, item) {
        lat = $(item).data('lat');
        lon = $(item).data('lon');
        var markerLocation = new L.LatLng(lat, lon);
        var marker = new L.Marker(markerLocation);

        // Clicking on a pointer makes others disappear if visible, or
        // otherwise appear.
        marker.on('click', function(e) {
            var val = $('#searchfield').val();
            var fullname = $(item).data('fullname');
            if (val != '') {
                search_string = '';
            }
            else {
                search_string = fullname;
            }
            $('#searchfield').val(search_string);
            $('#searchfield').trigger('input');
        });

        map.addLayer(marker);
        markers_array.push(marker);
    })
        }

function clear_map() {
    // Remove pointer layers from map.
    for (var marker in window.markers_array) {
        window.map.removeLayer(window.markers_array[marker]);
    }
    window.markers_array = [];
}

function redraw_grid() {
    // Redraw Reps grid.
    // Due to a bug in internet explorer we have to set clear:left css
    // attribute on some block-grid 's. Update each block to ensure that
    // only the leftest visible blocks get the extra attribute.
    $('.block-grid.two-up>li').css({'clear': ''});
    $('.block-grid.three-up>li').css({'clear': ''});
    $('.block-grid.four-up>li').css({'clear': ''});
    $('.block-grid.five-up>li').css({'clear': ''});

    $('.block-grid.two-up>li:visible').filter(
        function (index) {return index % 2 == 0;}).css('clear', 'left')
    $('.block-grid.three-up>li:visible').filter(
        function (index) {return index % 3 == 0;}).css('clear', 'left')
    $('.block-grid.four-up>li:visible').filter(
        function (index) {return index % 4 == 0;}).css('clear', 'left')
    $('.block-grid.five-up>li:visible').filter(
        function (index) {return index % 5 == 0;}).css('clear', 'left')
}

function set_number_of_reps(number_of_reps) {
    // Count and display the number of visible reps.
    $('#profiles-number-of-reps').html(number_of_reps);
    if (number_of_reps === 1) {
        $('#profiles-number-of-reps-plural').html('');
    }
    else {
        $('#profiles-number-of-reps-plural').html('s');
    }
}

var update_results = function(query) {
    return function(data) {
        // console.log('Updating results');
        $('#search-icon').html('s');

        if ($(location).attr('hash').substring(2) !== query) {
            // console.log('Values different', $(location).attr('hash').substring(2), query);
            return;
        }

        clear_map();
        $('#grid-search-list').empty();
        $('#table-search-list').empty();
        $('#gridItem').tmpl(data.objects).appendTo('#grid-search-list');
        redraw_grid();
        set_number_of_reps(data.meta.total_count);
        $('#listItem').tmpl(data.objects).appendTo('#table-search-list');
        $('#searchfield').data('searching', undefined);
        add_pointers();
    }
}

function request_error() {
    // Unset data-searching after half a second to deal with API timeouts.
    // console.log('Timeout');
    $('#searchfield').data('searching', undefined);
    $('#search-icon').html('s');
}

function set_dropdown_value(name, value) {
    $(name).val(value);
    // We have to force trigger 'change' for foundation to update.
    $(name).trigger('change');
}


function send_query() {
    value = $(location).attr('hash').substring(2);
    // console.log('Value', value);

    // Make sure we are not firing the same same request twice.
    if ($('#searchfield').data('searching') === value) {
        return;
    }

    $('#searchfield').data('searching', value)

    // Unbind change events to avoid triggering twice the same action.
    unbind_events();

    // console.log('Sending', value);

    // Form query based on URL
    extra_q = ''
    country = hash_get_value('country');
    set_dropdown_value('#adv-search-country', country);
    if (country) {
        extra_q += '&profile__country__iexact=' + country;
    }

    area = hash_get_value('area');
    set_dropdown_value('#adv-search-area', area);
    if (area) {
        extra_q += '&profile__functional_areas__name__iexact=' + area;
    }

    search = hash_get_value('search');
    $('#searchfield').val(search);
    if (search) {
        extra_q += '&query=' + search;
    }

    group = hash_get_value('group');
    set_dropdown_value('#adv-search-group', group);
    if (group) {
        extra_q += '&group=' + group;
    }

    // Abort previous request
    if (request) {
        // console.log(request.state());
        request.abort()
        // console.log(request.state());
    }
    request = $.ajax({
        url: '/api/v1/rep/?limit=0&order_by=profile__country,last_name,first_name' + extra_q,
        success: update_results(value),
        error: request_error
    });

    // Rebind events.
    bind_events();
}

function hash_set_value(key, value) {
    // Set value for key in hash
    hash = $(location).attr('hash').substring(2).toLowerCase().replace(/\/$/, '');
    // console.log(hash);
    if (hash.length > 0) {
        keys = hash.split('/').filter(function(element, index) { return (index % 2 == 0) });
        values = hash.split('/').filter(function(element, index) { return (index % 2 == 1) });
    }
    else {
        keys = [];
        values = [];
    }

    index_of_key = keys.indexOf(key);

    if (index_of_key > -1) {
        // console.log('Found', key);
        values[index_of_key] = value;
    }
    else {
        // console.log('Not Found', key);
        keys.push(key);
        values.push(value);
    }

    // console.log(hash.split('/'));
    // console.log('Keys', keys);
    // console.log('Values', values);
    hash = '/'
    for (var i=0; i < keys.length; i++) {
        // console.log(i, keys[i], values[i])
        if (values[i].length > 0 ) {
            hash += keys[i] + '/' + values[i] + '/'
        }
    }
    // console.log(hash);

    $(location).attr('hash', hash);
}

function hash_get_value(key) {
    // Get value for key in hash
    hash = $(location).attr('hash').substring(2).toLowerCase();
    keys = hash.split('/').filter(function(element, index) { return (index % 2 == 0) });
    values = hash.split('/').filter(function(element, index) { return (index % 2 == 1) });
    index_of_key = keys.indexOf(key)
    if (index_of_key > -1) {
        return values[index_of_key].toLowerCase();
    }

    return undefined
}

function bind_events() {
    // Bind events
    // console.log('Binding events');
    // Update hash, on search input update.
    $('#searchfield').bind('propertychange keyup input paste', function(event) {
        // Set icon.
        $('#search-icon').html('{');
        hash_set_value('search', $('#searchfield').val());
    });

    // Set advanced search events.
    $('#adv-search-group').change(function() {
        // Set icon.
        $('#search-icon').html('{');
        hash_set_value('group', $('#adv-search-group').val());
    });

    $('#adv-search-country').change(function() {
        // Set icon.
        $('#search-icon').html('{');
        hash_set_value('country', $('#adv-search-country').val());
    });

    $('#adv-search-area').change(function() {
        // Set icon.
        $('#search-icon').html('{');
        hash_set_value('area', $('#adv-search-area').val());
    });

    $(window).bind('hashchange', function(e) { send_query(); });
}

function unbind_events() {
    // Unbind events
    // console.log('Unbinding events');
    $('#searchfield').unbind('propertychange keyup input paste');
    $('#adv-search-country').unbind('change');
    $('#adv-search-group').unbind('change');
    $('#adv-search-area').unbind('change');
    $(window).unbind('hashchange');
}

$(document).ready(function () {
    initialize_map();

    view = hash_get_value('view');
    if (view == 'list') {
        $('#profiles_gridview').hide();
        $('#profiles_listview').show();
    }

    $('#searchform').submit(function (event) {
        event.preventDefault();
    });

    $('#listviewbutton').bind('click', function () {
        $('#profiles_listview').hide();
        $('#profiles_gridview').show();
        hash_set_value('view', 'grid');
        redraw_grid();
    });

    $('#gridviewbutton').bind('click', function () {
        $('#profiles_gridview').hide();
        $('#profiles_listview').show();
        hash_set_value('view', 'list');
    });

    // Show advanced search options if used in url.
    if (hash_get_value('group') || hash_get_value('area') || hash_get_value('country')) {
        $('#adv-search').show();
    }

    // Advanced button click.
    $('#adv-search-icon').click(function() {
        $('#adv-search').slideToggle();
    });

    // Set values to fields.
    set_dropdown_value('#adv-search-group', hash_get_value('group'));
    set_dropdown_value('#adv-search-area', hash_get_value('area'));
    set_dropdown_value('#adv-search-country', hash_get_value('country'));

    // Bind events.
    bind_events();

    // Enable search field when ready.
    $('#searchfield').attr('Placeholder', 'Filter using any keyword');
    $('#searchfield').removeAttr('disabled');
    $('#searchfield').val(hash_get_value('search'));

    send_query();
});
