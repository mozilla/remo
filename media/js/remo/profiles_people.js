var ProfilesLib = {};
ProfilesLib.markers_array = [];
ProfilesLib.map = undefined;
ProfilesLib.request = undefined;
ProfilesLib.number_of_reps = 0;
ProfilesLib.searchfield_elm = $('#searchfield');
ProfilesLib.gridview_elm = $('#profiles_gridview');
ProfilesLib.listview_elm = $('#profiles_listview');
ProfilesLib.noresults_elm = $('#profiles_noresults');
ProfilesLib.adv_search_country_elm = $('#adv-search-country');
ProfilesLib.adv_search_group_elm = $('#adv-search-group');
ProfilesLib.adv_search_area_elm = $('#adv-search-area');
ProfilesLib.search_icon_elm = $('#search-icon');
ProfilesLib.grid_search_list_elm = $('#grid-search-list');
ProfilesLib.table_search_list_elm = $('#table-search-list');
ProfilesLib.griditem_tmpl_elm = $('#gridItem-tmpl');
ProfilesLib.listitem_tmpl_elm = $('#listItem-tmpl');

function initialize_map() {
    // Initialize map.
    ProfilesLib.map = new L.Map('map', { minZoom: 1 });
    var attribution = ('Map data &copy; <a href="http://openstreetmap.org">' +
                       'OpenStreetMap</a> contributors, <a href="http://creativecommons.org/' +
                       'licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © ' +
                       '<a href="http://cloudmade.com">CloudMade</a>');
    var cloudmade = new L.TileLayer('http://{s}.tile.cloudmade.com/' +
                                    'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                    '997/256/{z}/{x}/{y}.png',
                                    { attribution: attribution, maxZoom: 18 });
    var center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    ProfilesLib.map.setView(center, 2).addLayer(cloudmade);

    // When user clicks on map and a search filter exists, remove filter.
    ProfilesLib.map.on('click', function(e) {
        var val = ProfilesLib.searchfield_elm.val();
        if (val !== '') {
            search_string = '';
            ProfilesLib.searchfield_elm.val(search_string);
            ProfilesLib.searchfield_elm.trigger('input');
        }
    });
}


function add_pointers() {
    // Add user pointers on map.
    $('.profiles-li-item').each(function(index, item) {
        var lat = $(item).data('lat');
        var lon = $(item).data('lon');
        var markerLocation = new L.LatLng(lat, lon);
        var marker = new L.Marker(markerLocation);

        // Clicking on a pointer makes others disappear if visible, or
        // otherwise appear.
        marker.on('click', function(e) {
            var val = ProfilesLib.searchfield_elm.val();
            var fullname = $(item).data('fullname');
            if (val !== '') {
                search_string = '';
            }
            else {
                search_string = fullname;
            }
            ProfilesLib.searchfield_elm.val(search_string);
            ProfilesLib.searchfield_elm.trigger('input');
        });

        ProfilesLib.map.addLayer(marker);
        ProfilesLib.markers_array.push(marker);
    });
}


function clear_map() {
    // Remove pointer layers from map.
    for (var marker in ProfilesLib.markers_array) {
        ProfilesLib.map.removeLayer(ProfilesLib.markers_array[marker]);
    }
    ProfilesLib.markers_array = [];
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
        function (index) {return index % 2 === 0;}).css('clear', 'left');
    $('.block-grid.three-up>li:visible').filter(
        function (index) {return index % 3 === 0;}).css('clear', 'left');
    $('.block-grid.four-up>li:visible').filter(
        function (index) {return index % 4 === 0;}).css('clear', 'left');
    $('.block-grid.five-up>li:visible').filter(
        function (index) {return index % 5 === 0;}).css('clear', 'left');
}

function set_number_of_reps(number_of_reps) {
    // Count and display the number of visible reps.
    number_of_reps = parseInt(number_of_reps, 10);
    ProfilesLib.number_of_reps = number_of_reps;

    if (number_of_reps === 0) {
        $('#profiles-reps-number').hide();
    }
    else {
        $('#profiles-reps-number').show();
        if (number_of_reps === 1) {
            $('#profiles-number-of-reps').html(number_of_reps + ' Rep found.');
        }
        else {
            $('#profiles-number-of-reps').html(number_of_reps + ' Reps found.');
        }
    }
}


var update_results = function(query) {
    return function(data) {
        // console.log('Updating results');
        if ($(location).attr('hash').substring(2) !== query) {
            // console.log('Values different', $(location).attr('hash').substring(2), query);
            return;
        }

        ProfilesLib.search_icon_elm.html('s');

        clear_map();
        ProfilesLib.grid_search_list_elm.empty();
        ProfilesLib.table_search_list_elm.empty();

        set_number_of_reps(data.meta.total_count);

        var view = hash_get_value('view');
        switch_views(view);

        ProfilesLib.griditem_tmpl_elm.tmpl(data.objects).appendTo('#grid-search-list');
        redraw_grid();
        ProfilesLib.listitem_tmpl_elm.tmpl(data.objects).appendTo('#table-search-list');
        ProfilesLib.searchfield_elm.data('searching', undefined);
        add_pointers();
    };
};


function request_error(query, status) {
    // Unset data-searching after half a second to deal with API timeouts.
    // console.log('Request error:', status);
    if (status !== 'abort') {
        ProfilesLib.searchfield_elm.data('searching', undefined);
        ProfilesLib.search_icon_elm.html('s');
    }
}


function set_dropdown_value(elm, value) {
    elm.val(value);
    // We have to force trigger 'change' for foundation to update.
    elm.trigger('change');
}


function send_query() {
    var extra_q = '';
    var csv = false;
    var API_URL = '/api/v1/rep/?limit=0&order_by=profile__country,last_name,first_name';
    var value = $(location).attr('hash').substring(2);
    // console.log('Value', value);

    // Make sure we are not firing the same same request twice.
    if (ProfilesLib.searchfield_elm.data('searching') === value) {
        return;
    }

    // Set icon.
    ProfilesLib.search_icon_elm.html('{');

    ProfilesLib.searchfield_elm.data('searching', value);

    // Unbind change events to avoid triggering twice the same action.
    unbind_events();

    // console.log('Sending', value);

    // Form query based on URL
    var country = hash_get_value('country');
    set_dropdown_value(ProfilesLib.adv_search_country_elm, country);
    if (country) {
        extra_q += '&profile__country__iexact=' + country;
    }

    var area = hash_get_value('area');
    set_dropdown_value(ProfilesLib.adv_search_area_elm, area);
    if (area) {
        extra_q += '&profile__functional_areas__name__iexact=' + area;
    }

    var search = hash_get_value('search');
    ProfilesLib.searchfield_elm.val(search);
    if (search) {
        extra_q += '&query=' + search;
    }

    var group = hash_get_value('group');
    set_dropdown_value(ProfilesLib.adv_search_group_elm, group);
    if (group) {
        extra_q += '&group=' + group;
    }

    var format = hash_get_value('format');
    if (format && format == 'csv') {
        csv = true;
        extra_q += '&format=csv';
    }

    if (!csv) {
        // Abort previous request
        if (ProfilesLib.request) {
            // console.log(request.state());
            ProfilesLib.request.abort();
            // console.log(request.state());
        }
        ProfilesLib.request = $.ajax({
            url: API_URL + extra_q,
            success: update_results(value),
            error: request_error,
            timeout: 30000
        });
    }
    else {
        window.location = API_URL + extra_q;
    }

    // Rebind events.
    bind_events();

    if (csv) {
        // Remove CSV export variable to also load results in the
        // page. We do this change after bind_events() we can actually
        // capture this event.
        hash_set_value('format', '');

        // Save current map zoom and center
        var zoom = ProfilesLib.map.getZoom();
        var center = ProfilesLib.map.getCenter();

        // We shouldn't touch "private" variables but this is to force
        // map to reload tiles. When a user hits the CSV export page,
        // tile loading is interrupted by the change of
        // window.location. By re-setting map's view (setView) we
        // force tile loading.
        ProfilesLib.map._zoom = -1;
        ProfilesLib.map.setView(center, zoom);
    }
}

function hash_set_value(key, value) {
    // Set value for key in hash
    var hash = $(location).attr('hash').substring(2).toLowerCase().replace(/\/$/, '');
    var keys;
    var values;

    if (value === undefined) {
        value = '';
    }

    // console.log('Hash:', hash);
    if (hash.length > 0) {
        keys = hash.split('/').filter(function(element, index) { return (index % 2 === 0); });
        values = hash.split('/').filter(function(element, index) { return (index % 2 === 1); });
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
    hash = '/';
    for (var i=0; i < keys.length; i++) {
        // console.log(i, keys[i], values[i])
        if (values[i].length > 0 ) {
            hash += keys[i] + '/' + values[i] + '/';
        }
    }
    // console.log(hash);

    $(location).attr('hash', hash);
}

function hash_get_value(key) {
    // Get value for key in hash
    var hash = $(location).attr('hash').substring(2).toLowerCase();
    var keys = hash.split('/').filter(function(element, index) { return (index % 2 === 0); });
    var values = hash.split('/').filter(function(element, index) { return (index % 2 === 1); });
    var index_of_key = keys.indexOf(key);
    if (index_of_key > -1) {
        return values[index_of_key].toLowerCase();
    }

    return;
}

function bind_events() {
    // Bind events
    // console.log('Binding events');
    // Update hash, on search input update.
    ProfilesLib.searchfield_elm.bind('propertychange keyup input paste', function(event) {
        hash_set_value('search', ProfilesLib.searchfield_elm.val());
    });

    // Set advanced search events.
    ProfilesLib.adv_search_group_elm.change(function() {
        hash_set_value('group', ProfilesLib.adv_search_group_elm.val());
    });

    ProfilesLib.adv_search_country_elm.change(function() {
        hash_set_value('country', ProfilesLib.adv_search_country_elm.val());
    });

    ProfilesLib.adv_search_area_elm.change(function() {
        hash_set_value('area', ProfilesLib.adv_search_area_elm.val());
    });

    $(window).bind('hashchange', function(e) { send_query(); });
}

function switch_views(view) {
    unbind_events();
    if (ProfilesLib.number_of_reps === 0) {
        ProfilesLib.gridview_elm.hide();
        ProfilesLib.listview_elm.hide();
        ProfilesLib.noresults_elm.show();
    }
    else if (view === 'list') {
        ProfilesLib.noresults_elm.hide();
        ProfilesLib.gridview_elm.hide();
        ProfilesLib.listview_elm.show();
    }
    else {
        ProfilesLib.noresults_elm.hide();
        ProfilesLib.listview_elm.hide();
        ProfilesLib.gridview_elm.show();
    }
    hash_set_value('view', view);
    bind_events();
}

function unbind_events() {
    // Unbind events
    // console.log('Unbinding events');
    ProfilesLib.searchfield_elm.unbind('propertychange keyup input paste');
    ProfilesLib.adv_search_country_elm.unbind('change');
    ProfilesLib.adv_search_group_elm.unbind('change');
    ProfilesLib.adv_search_area_elm.unbind('change');
    $(window).unbind('hashchange');
}

$(document).ready(function () {
    initialize_map();

    var view = hash_get_value('view');
    if (view === 'list') {
        ProfilesLib.gridview_elm.hide();
        ProfilesLib.listview_elm.show();
    }

    $('#searchform').submit(function (event) {
        event.preventDefault();
    });

    $('#listviewbutton').bind('click', function () {
        switch_views('list');
    });

    $('#gridviewbutton').bind('click', function () {
        switch_views('grid');
    });

    // Show advanced search options if used in url.
    if (hash_get_value('group') || hash_get_value('area') || hash_get_value('country')) {
        $('#adv-search').show();
    }

    // Advanced button click.
    $('#adv-search-icon').click(function() {
        $('#adv-search').slideToggle();
    });

    // Export to CSV click.
    $('#csv-export-button').click(function() {
        hash_set_value('format', 'csv');
    });

    // Set values to fields.
    set_dropdown_value(ProfilesLib.adv_search_group_elm, hash_get_value('group'));
    set_dropdown_value(ProfilesLib.adv_search_area_elm, hash_get_value('area'));
    set_dropdown_value(ProfilesLib.adv_search_country_elm, hash_get_value('country'));

    // Bind events.
    bind_events();

    // Enable search field when ready.
    ProfilesLib.searchfield_elm.attr('Placeholder', 'Filter using any keyword');
    ProfilesLib.searchfield_elm.removeAttr('disabled');
    ProfilesLib.searchfield_elm.val(hash_get_value('search'));

    send_query();
});
