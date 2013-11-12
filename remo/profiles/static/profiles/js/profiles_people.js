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
ProfilesLib.search_ready_icon_elm = $('#search-ready-icon');
ProfilesLib.search_loading_icon_elm = $('#search-loading-icon');
ProfilesLib.grid_search_list_elm = $('#grid-search-list');
ProfilesLib.table_search_list_elm = $('#table-search-list');
ProfilesLib.griditem_tmpl_elm = $('#gridItem-tmpl');
ProfilesLib.listitem_tmpl_elm = $('#listItem-tmpl');
ProfilesLib.profiles_loading_wrapper_elm = $('#profiles-loading-wrapper');
ProfilesLib.window_elm = $(window);
ProfilesLib.location_elm = $(location);
ProfilesLib.window_offset = 450;
ProfilesLib.results_batch = 21;
ProfilesLib.offset = 0;
ProfilesLib.limited = true;
ProfilesLib.allset = false;
ProfilesLib.trigger_timeout = undefined;
ProfilesLib.api_csv_url = undefined;

var MAPBOX_TOKEN = $('body').data('mapbox-token');

function initialize_map() {
    // Initialize map.
    var center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    ProfilesLib.map = new L.mapbox.map('map', MAPBOX_TOKEN, {minZoom: 1});
    ProfilesLib.map.setView(center, 2);

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
    // If results are limited read lat/lon values from .profile-pointer-item
    var pointer_list = $('.profiles-li-item');
    if (ProfilesLib.limited) {
        pointer_list = $('.profile-pointer-item');
    }

    // Add user pointers on map.
    pointer_list.each(function(index, item) {
        var lat = $(item).data('lat');
        var lon = $(item).data('lon');
        var markerLocation = new L.LatLng(lat, lon);
        var marker = new L.Marker(markerLocation);

        // Clicking on a pointer makes others disappear if visible, or
        // otherwise appear.
        marker.on('click', function(e) {
            var val = ProfilesLib.searchfield_elm.val();
            var fullname = $(item).data('fullname').toLowerCase();
            if (val === fullname) {
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
    // Display the number of visible reps.
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


var update_results = function(data, query, newquery, update_pointers) {
    if (ProfilesLib.location_elm.attr('hash').substring(2) !== query) {
        return;
    }

    ProfilesLib.search_loading_icon_elm.hide();
    ProfilesLib.search_ready_icon_elm.show();

    if (newquery) {
        clear_map();
        ProfilesLib.grid_search_list_elm.empty();
        ProfilesLib.table_search_list_elm.empty();
    }

    if ((parseInt(data.meta.limit, 10) === 0) ||
        (parseInt(data.meta.offset, 10) + ProfilesLib.results_batch >= parseInt(data.meta.total_count, 10))) {
        ProfilesLib.allset = true;
        ProfilesLib.profiles_loading_wrapper_elm.hide();
    }
    else {
        ProfilesLib.offset = parseInt(data.meta.offset, 10) + ProfilesLib.results_batch;
    }

    set_number_of_reps(data.meta.total_count);

    var view = hash_get_value('view');
    switch_views(view);

    if (view === 'list') {
        ProfilesLib.listitem_tmpl_elm.tmpl(data.objects).appendTo('#table-search-list');
    }
    else {
        ProfilesLib.griditem_tmpl_elm.tmpl(data.objects).appendTo('#grid-search-list');
        redraw_grid();
    }

    ProfilesLib.searchfield_elm.data('searching', undefined);
    if (update_pointers) {
        setTimeout(function() { add_pointers(); }, 500);
    }
};


function request_error() {
    // Unset data-searching after half a second to deal with API timeouts.
    ProfilesLib.searchfield_elm.data('searching', undefined);
    ProfilesLib.search_loading_icon_elm.hide();
    ProfilesLib.search_ready_icon_elm.show();
    ProfilesLib.profiles_loading_wrapper_elm.hide();
}

function handle_xhr_response(value, newquery, update_pointers) {

    return function(event) {
        if (ProfilesLib.request.status === 200) {
            update_results(JSON.parse(ProfilesLib.request.responseText), value, newquery, update_pointers);
        }
        else {
            request_error();
        }
    };
}

function send_query(newquery) {
    var extra_q = '';
    var update_pointers = true;
    if (newquery) {
        ProfilesLib.allset = false;
        ProfilesLib.offset = 0;
    }
    else {
        newquery = false;
    }
    ProfilesLib.limited = false;
    var API_CSV_URL = '/api/v1/rep/?order_by=profile__country,last_name,first_name&offset=0&limit=0';
    var API_URL = '/api/v1/rep/?order_by=profile__country,last_name,first_name&offset='+ ProfilesLib.offset;
    var value = ProfilesLib.location_elm.attr('hash').substring(2);


    // Make sure we are not firing the same same request twice.
    if ((ProfilesLib.searchfield_elm.data('searching') === API_URL && !newquery) || (!newquery && ProfilesLib.allset)) {
        return;
    }

    // Show bottom loading icon.
    ProfilesLib.profiles_loading_wrapper_elm.show();

    ProfilesLib.searchfield_elm.data('searching', API_URL);

    // Unbind change events to avoid triggering twice the same action.
    unbind_events();

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

    csv_q = extra_q;

    if (!country && !area && !search && !group) {
        ProfilesLib.limited = true;
        extra_q += '&limit=' + ProfilesLib.results_batch;
        if (ProfilesLib.offset !== 0) {
            update_pointers = false;
        }
    }
    else {
        extra_q += '&limit=0';
    }

    // Abort previous request
    if (ProfilesLib.request) {
        ProfilesLib.request.abort();
    }

    ProfilesLib.request = $.ajax({
        url: API_URL + extra_q,
        type: 'GET',
        dataType: 'json'
    });
    ProfilesLib.request.done(handle_xhr_response(value, newquery, update_pointers));
    ProfilesLib.request.fail(request_error);

    // Set the CSV url
    ProfilesLib.api_csv_url = API_CSV_URL + csv_q + '&format=csv';

    // Rebind events.
    bind_events();

}

function switch_views(view) {
    unbind_events();
    if (ProfilesLib.number_of_reps === 0) {
        $('#profiles_gridview').hide();
        $('#profiles_listview').hide();
        $('#profiles_noresults').show();
    }
    else if (view === 'list') {
        $('#profiles_noresults').hide();
        $('#profiles_gridview').hide();
        $('#profiles_listview').show();
    }
    else {
        $('#profiles_noresults').hide();
        $('#profiles_listview').hide();
        $('#profiles_gridview').show();
    }
    hash_set_value('view', view);
    bind_events();
}

function bind_events() {
    // Bind events
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

    ProfilesLib.window_elm.bind('hashchange', function(e) {
        // Set icon.
        ProfilesLib.search_ready_icon_elm.hide();
        ProfilesLib.search_loading_icon_elm.show();

        clearTimeout(ProfilesLib.trigger_timeout);
        ProfilesLib.trigger_timeout = setTimeout(function() {
            send_query(newquery=true);
        }, 400);
    });
}

function unbind_events() {
    // Unbind events
    ProfilesLib.searchfield_elm.unbind('propertychange keyup input paste');
    ProfilesLib.adv_search_country_elm.unbind('change');
    ProfilesLib.adv_search_group_elm.unbind('change');
    ProfilesLib.adv_search_area_elm.unbind('change');
    ProfilesLib.window_elm.unbind('hashchange');
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

function loader_canvas_icon_init() {
    // Initialize bottom loader.
    var cl = new CanvasLoader('profiles-loading');
    cl.setColor('#888888'); // default is '#000000'
    cl.setDiameter(24); // default is 40
    cl.setDensity(30); // default is 40
    cl.setRange(0.8); // default is 1.3
    cl.setFPS(23); // default is 24
    cl.show(); // Hidden by default

    // Initialize search loader.
    var sl = new CanvasLoader('search-loading-icon');
    sl.setColor('#888888'); // default is '#000000'
    sl.setDiameter(24); // default is 40
    sl.setDensity(30); // default is 40
    sl.setRange(0.8); // default is 1.3
    sl.setFPS(23); // default is 24
    sl.show(); // Hidden by default
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
        window.open(ProfilesLib.api_csv_url);
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

    // Set infinite scroll.
    ProfilesLib.window_elm.scroll(function(){
        if  (ProfilesLib.window_elm.scrollTop() >= $(document).height() -
             ProfilesLib.window_elm.height() - ProfilesLib.window_offset){
            send_query();
        }
    });

    loader_canvas_icon_init();
});
