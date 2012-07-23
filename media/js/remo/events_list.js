var EventsLib = {};
EventsLib.markers_array = [];
EventsLib.request = undefined;
EventsLib.number_of_events = 0;
EventsLib.searchform_elm = $('#searchform');
EventsLib.searchfield_elm = $('#searchfield');
EventsLib.search_icon_elm = $('#search-icon');
EventsLib.events_table_body_elm = $('#events-table-body');
EventsLib.eventsitem_tmpl_elm = $('#eventItem-tmpl');
EventsLib.period_selector_elm = $('#events-period-selector');
EventsLib.events_number_elm = $('#events-number');
EventsLib.events_table_elm = $('#events-table');

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
            var name = $(item).data('name');
            if (val !== '') {
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

    $(window).bind('hashchange', function(e) { send_query(); });
}

function unbind_events() {
    // Unbind events
    EventsLib.searchfield_elm.unbind('propertychange keyup input paste');
    EventsLib.period_selector_elm.unbind('change');
    $(window).unbind('hashchange');
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
    if (status !== 'abort') {
        EventsLib.searchfield_elm.data('searching', undefined);
        EventsLib.search_icon_elm.html('s');
    }
}


var update_results = function(query) {
    return function(data) {
        if ($(location).attr('hash').substring(2) !== query) {
            return;
        }

        EventsLib.search_icon_elm.html('s');

        clear_map();
        EventsLib.events_table_body_elm.empty();

        set_number_of_events(data.meta.total_count);

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
        add_pointers();
    };
};

function UTCDateString(d){
    return (d.getUTCFullYear() + '-' +
            pad2(d.getUTCMonth() + 1) + '-' +
            pad2(d.getUTCDate() +1 ));
}


function send_query() {
    var extra_q = '';
    var API_URL = '/api/v1/event/?limit=0';
    var value = $(location).attr('hash').substring(2);

    // Make sure we are not firing the same same request twice.
    if (EventsLib.searchfield_elm.data('searching') === value) {
        return;
    }

    // Set icon.
    EventsLib.search_icon_elm.html('<div id="floatingCirclesG"><div class="f_circleG" id="frotateG_01">' +
        '</div><div class="f_circleG" id="frotateG_02"></div><div class="f_circleG" id="frotateG_03">' +
        '</div><div class="f_circleG" id="frotateG_04"></div><div class="f_circleG" id="frotateG_05">' +
        '</div><div class="f_circleG" id="frotateG_06"></div><div class="f_circleG" id="frotateG_07">' +
        '</div><div class="f_circleG" id="frotateG_08"></div></div>');

    EventsLib.searchfield_elm.data('searching', value);

    // Unbind change events to avoid triggering twice the same action.
    unbind_events();

    // Period selector.
    var period = hash_get_value('period');
    set_dropdown_value(EventsLib.period_selector_elm, period);
    if (period) {
        var today = new Date();
        var today_utc_string = UTCDateString(today);
        if (period === 'future') {
            extra_q += '&start__gte=' + today_utc_string;
        }
        else if (period === 'past') {
            extra_q += '&start__lt=' + today_utc_string;
        }
        else if (period === 'all') {
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
    EventsLib.request = $.ajax({
        url: API_URL + extra_q,
        success: update_results(value),
        error: request_error,
        timeout: 30000
    });

    // Rebind events.
    bind_events();
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
});
