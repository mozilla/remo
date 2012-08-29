var EventsLib = {};
EventsLib.markers_array = [];
EventsLib.request = undefined;
EventsLib.number_of_events = 0;
EventsLib.searchform_elm = $('#searchform');
EventsLib.searchfield_elm = $('#searchfield');
EventsLib.events_table_body_elm = $('#events-table-body');
EventsLib.eventsitem_tmpl_elm = $('#eventItem-tmpl');
EventsLib.period_selector_elm = $('#events-period-selector');
EventsLib.events_number_elm = $('#events-number');
EventsLib.events_table_elm = $('#events-table');
EventsLib.search_loading_icon_elm = $('#search-loading-icon');
EventsLib.search_ready_icon_elm = $('#search-ready-icon');
EventsLib.events_loading_wrapper_elm = $('#events-loading-wrapper');
EventsLib.map_overlay_elm = $('#map-overlay');
EventsLib.window_elm = $(window);
EventsLib.location_elm = $(location);
EventsLib.trigger_timeout = undefined;
EventsLib.allset = false;
EventsLib.offset = 0;
EventsLib.window_offset = 450;
EventsLib.results_batch = 21;

function initialize_map() {
    // Initialize map.
    EventsLib.map = new L.Map('map', { minZoom: 1 });
    var attribution = ('Map data &copy; <a href="http://openstreetmap.org">' +
                       'OpenStreetMap</a> contributors, <a href="http://creativecommons.org/' +
                       'licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © ' +
                       '<a href="http://cloudmade.com">CloudMade</a>');
    var cloudmade = new L.TileLayer('http://{s}.tile.cloudmade.com/' +
                                    'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                    '997/256/{z}/{x}/{y}.png',
                                    { attribution: attribution, maxZoom: 18 });
    var center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    EventsLib.map.setView(center, 2).addLayer(cloudmade);

    // When user clicks on map and a search filter exists, remove filter.
    EventsLib.map.on('click', function(e) {
        var val = EventsLib.searchfield_elm.val();
        if (val !== '') {
            search_string = '';
            EventsLib.searchfield_elm.val(search_string);
            EventsLib.searchfield_elm.trigger('input');
        }
    });
}

function clear_map() {
    // Remove pointer layers from map.
    for (var marker in EventsLib.markers_array) {
        EventsLib.map.removeLayer(EventsLib.markers_array[marker]);
    }
    EventsLib.markers_array = [];
}

function add_pointers() {
    // Add user pointers on map.
    $('.event-item').each(function(index, item) {
        var lat = $(item).data('lat');
        var lon = $(item).data('lon');
        var markerLocation = new L.LatLng(lat, lon);
        var marker = new L.Marker(markerLocation);

        // Clicking on a pointer makes others disappear if visible, or
        // otherwise appear.
        marker.on('click', function(e) {
            var val = EventsLib.searchfield_elm.val();
            var name = $(item).data('name').toString();
            if (val === name) {
                search_string = '';
            }
            else {
                search_string = name;
            }
            EventsLib.searchfield_elm.val(search_string);
            EventsLib.searchfield_elm.trigger('input');
        });
        EventsLib.map.addLayer(marker);
        EventsLib.markers_array.push(marker);
    });
}

function bind_events() {
    // Bind events
    // Update hash, on search input update.
    EventsLib.searchfield_elm.bind('propertychange keyup input paste', function(event) {
        hash_set_value('search', EventsLib.searchfield_elm.val());
    });

    EventsLib.period_selector_elm.change(function() {
        hash_set_value('period', EventsLib.period_selector_elm.val());
    });

    EventsLib.window_elm.bind('hashchange', function(e) {
        // Set icon.
        EventsLib.search_ready_icon_elm.hide();
        EventsLib.search_loading_icon_elm.show();

        clearTimeout(EventsLib.trigger_timeout);
        EventsLib.trigger_timeout = setTimeout(function() {
            send_query(newquery=true);
        }, 400);
    });
}

function unbind_events() {
    // Unbind events
    EventsLib.searchfield_elm.unbind('propertychange keyup input paste');
    EventsLib.period_selector_elm.unbind('change');
    EventsLib.window_elm.unbind('hashchange');
}

function set_number_of_events(number_of_events) {
    // Display the number of visible reps.
    number_of_events = parseInt(number_of_events, 10);
    EventsLib.number_of_events = number_of_events;

    if (number_of_events === 0) {
        EventsLib.events_table_elm.hide();
        EventsLib.events_number_elm.html('Sorry no events found.');
    }
    else {
        EventsLib.events_table_elm.show();

        if (number_of_events === 1) {
            EventsLib.events_number_elm.html('1 event found.');
        }
        else {
            EventsLib.events_number_elm.html(number_of_events + ' events found.');
        }
    }
}

function request_error(query, status) {
    // Unset data-searching after half a second to deal with API timeouts.
    EventsLib.searchfield_elm.data('searching', undefined);
    EventsLib.search_loading_icon_elm.hide();
    EventsLib.search_ready_icon_elm.show();
    EventsLib.events_loading_wrapper_elm.hide();
}

function handle_xhr_response(value, newquery, past_events) {
    return function(event) {
        if (EventsLib.request.status === 200) {
            update_results(JSON.parse(EventsLib.request.responseText), value, newquery, past_events);
        }
        else {
            request_error();
        }
    };
}

var update_results = function(data, query, newquery, past_events) {
    if (EventsLib.location_elm.attr('hash').substring(2) !== query) {
        return;
    }

    EventsLib.search_loading_icon_elm.hide();
    EventsLib.search_ready_icon_elm.show();
    EventsLib.events_loading_wrapper_elm.hide();

    if (newquery) {
        clear_map();
        EventsLib.events_table_body_elm.empty();
        set_number_of_events(data.meta.total_count);
    }

    if (parseInt(data.meta.offset, 10) + EventsLib.results_batch >= data.meta.total_count) {
        EventsLib.allset = true;
    }
    else {
        EventsLib.offset = parseInt(data.meta.offset, 10) + EventsLib.results_batch;
    }

    EventsLib.eventsitem_tmpl_elm.tmpl(data.objects, {
        getDay: function() {
            var s = new Date(this.data.local_start);

            if (this.data.multiday) {
                var e = new Date(this.data.local_end);
                return s.getDate() + '-' + e.getDate();
            }

            return s.getDate();
        },
        getMonth: function() {
            var monthNames = [ "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                               "JUL", "AUG", "SEP", "OCT", "NOV", "DEC" ];

            if (this.data.multiday) {
                var s = new Date(this.data.local_start);
                var e = new Date(this.data.local_end);

                // Also check if multimonth
                if (this.is_multimonth()) {
                    return monthNames[s.getMonth()] + '-' + monthNames[e.getMonth()];
                }
            }
            d = new Date(this.data.local_start);
            return monthNames[d.getMonth()];

        },
        is_multimonth: function() {
            var s = new Date(this.data.local_start);
            var e = new Date(this.data.local_end);
            return s.getMonth() != e.getMonth();
        }
    }).appendTo('#events-table-body');

    EventsLib.searchfield_elm.data('searching', undefined);

    if (past_events && parseInt(data.meta.total_count, 10) > EventsLib.results_batch) {
        EventsLib.map_overlay_elm.show();
    }
    else {
        EventsLib.map_overlay_elm.hide();
        setTimeout(function() { add_pointers(); }, 500);
    }
};

function UTCDateString(d){
    return (d.getUTCFullYear() + '-' +
            pad2(d.getUTCMonth() + 1) + '-' +
            pad2(d.getUTCDate()));
}


function send_query(newquery) {
    var past_events = true;
    var extra_q = '';
    var value = EventsLib.location_elm.attr('hash').substring(2);

    if (newquery) {
        EventsLib.allset = false;
        EventsLib.offset = 0;
    }
    else {
        newquery = false;
    }
    var API_URL = '/api/v1/event/?offset=' + EventsLib.offset;

    if ((EventsLib.searchfield_elm.data('searching') === API_URL && !newquery) || (!newquery && EventsLib.allset)) {
        return;
    }

    // Show bottom loading icon.
    EventsLib.events_loading_wrapper_elm.show();

    EventsLib.searchfield_elm.data('searching', API_URL);

    // Unbind change events to avoid triggering twice the same action.
    unbind_events();

    // Period selector.
    var period = hash_get_value('period');
    set_dropdown_value(EventsLib.period_selector_elm, period);
    if (period) {
        var today = new Date();
        var today_utc_string = UTCDateString(today);
        if (period === 'future') {
            extra_q += '&limit=0';
            extra_q += '&start__gte=' + today_utc_string;
            past_events = false;
        }
        else if (period === 'past') {
            extra_q += '&limit=' + EventsLib.results_batch;
            extra_q += '&start__lt=' + today_utc_string;
        }
        else if (period === 'all') {
            extra_q += '&limit=' + EventsLib.results_batch;
            extra_q += '&start__gt=1970-01-01';
        }
    }

    // Search term.
    var search = hash_get_value('search');
    EventsLib.searchfield_elm.val(search);
    if (search) {
        extra_q += '&query=' + search;
    }

    // Abort previous request
    if (EventsLib.request) {
        EventsLib.request.abort();
    }
    EventsLib.request = new XMLHttpRequest();
    EventsLib.request.open('GET', API_URL + extra_q, true);
    EventsLib.request.onload = handle_xhr_response(value, newquery, past_events);
    EventsLib.request.onerror = request_error;
    EventsLib.request.send();

    // Rebind events.
    bind_events();
}

function loader_canvas_icon_init() {
    // Initialize bottom loader.
    var cl = new CanvasLoader('events-loading');
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

    EventsLib.searchform_elm.submit(function (event) {
        event.preventDefault();
    });

    var period = hash_get_value('period');
    if (!period) {
        period = 'future';
        hash_set_value('period', period);
    }

    // Set values to fields.
    set_dropdown_value(EventsLib.period_selector_elm, period);

    // Bind events.
    bind_events();

    // Enable search field when ready.
    EventsLib.searchfield_elm.attr('Placeholder', 'Filter using any keyword');
    EventsLib.searchfield_elm.removeAttr('disabled');
    EventsLib.searchfield_elm.val(hash_get_value('search'));

    send_query();

    loader_canvas_icon_init();

    // Leaflet is loaded, so move map overlay into map div.
    EventsLib.map_overlay_elm.appendTo('#map');

    // Set infinite scroll.
    EventsLib.window_elm.scroll(function(){
        if  (EventsLib.window_elm.scrollTop() >=
             $(document).height() - EventsLib.window_elm.height() - EventsLib.window_offset) {
            send_query(newquery=false);
        }
    });
});
