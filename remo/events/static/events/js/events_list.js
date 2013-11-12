var EventsLib = {};
EventsLib.markers_array = [];
EventsLib.request = undefined;
EventsLib.number_of_events = 0;
EventsLib.searchform_elm = $('#searchform');
EventsLib.searchfield_elm = $('#searchfield');
EventsLib.events_table_body_elm = $('#events-table-body');
EventsLib.eventsitem_tmpl_elm = $('#eventItem-tmpl');
EventsLib.period_selector_elm = $('#events-period-selector');
EventsLib.category_selector_elm = $('#adv-search-categories');
EventsLib.events_number_elm = $('#events-number');
EventsLib.events_table_elm = $('#events-table');
EventsLib.search_loading_icon_elm = $('#search-loading-icon');
EventsLib.search_ready_icon_elm = $('#search-ready-icon');
EventsLib.events_loading_wrapper_elm = $('#events-loading-wrapper');
EventsLib.map_overlay_elm = $('#map-overlay');
EventsLib.datepicker_start_elm = $('#date-start');
EventsLib.datepicker_end_elm = $('#date-end');
EventsLib.multi_e_ical_elm = $('#icalendar-export-button');
EventsLib.adv_search_elm = $('#adv-search');
EventsLib.adv_search_icon_elm = $('#adv-search-icon-events');
EventsLib.datepicker_elm = $('.datepicker');
EventsLib.timeline_overlay_elm = $('#timeline-overlay');
EventsLib.event_timeline_elm = $('#event-timeline');
EventsLib.window_elm = $(window);
EventsLib.location_elm = $(location);
EventsLib.trigger_timeout = undefined;
EventsLib.allset = false;
EventsLib.offset = 0;
EventsLib.window_offset = 450;
EventsLib.results_batch = 21;

var MAPBOX_TOKEN = $('body').data('mapbox-token');

function initialize_map() {
    // Initialize map.
    var center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    EventsLib.map = L.mapbox.map('map', MAPBOX_TOKEN, {minZoom: 1});
    EventsLib.map.setView(center, 2);

    L.control.locate({
        setView: false,
        onLocationError: handleLocationError,
        locateOptions: {
            watch: false
        }
    }).addTo(EventsLib.map);

    EventsLib.map.on('locationfound', handleLocationFound);

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

function handleLocationError() {
    // Show message when geolocation fails
    var msg = 'Sorry, we could not determine your location.';
    showMessage({
        'msg': msg,
        'tag': 'warning'
    });
}

function handleLocationFound(e) {
    // setView and zoom map when geolocation succeeds
    EventsLib.map.setView(e.latlng, 5);
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

function dateFormatter(date) {
    var day = date.getDate();
    var month = date.getMonth() + 1;
    var year = date.getFullYear();
    return year + ',' + month + ',' + day;
}

function initialize_timeline(events, enable) {
    var event_timeline = {};
    var timeline = {};
    timeline.headline = 'Events';
    timeline.type = 'default';

    if (enable && events.objects.length > 0) {
        var dates = [];
        events.objects.forEach(function(item) {
            var start = Date.parse(item.start);
            var date_start = new Date(start);
            var end  = Date.parse(item.end);
            var date_end = new Date(end);

            var elm = {};
            elm.startDate = dateFormatter(date_start);
            elm.endDate = dateFormatter(date_end);
            elm.headline = '<a href="'+item.event_url+'">'+item.name+'</a>';

            dates.push(elm);
        });

        timeline.date = dates;
        event_timeline.timeline = timeline;

        EventsLib.event_timeline_elm.empty();
        EventsLib.timeline_overlay_elm.appendTo(EventsLib.event_timeline_elm);
        EventsLib.timeline_overlay_elm.hide();
        createStoryJS({type:       'timeline',
                       width:      '980',
                       height:     '300',
                       source:     event_timeline,
                       embed_id:   'event-timeline',
                       debug:      false});
    } else {
        EventsLib.event_timeline_elm.empty();
        EventsLib.timeline_overlay_elm.appendTo(EventsLib.event_timeline_elm);
        EventsLib.timeline_overlay_elm.show();
    }
}

function show_timeline() {
    var enable = false;
    var data;
    var period = hash_get_value('period');
    var valid_period = $.inArray(period, ['custom', 'future']);

    if (EventsLib.allset) {
        data = JSON.parse(EventsLib.request.responseText);
        enable = (parseInt(data.meta.total_count, 10) < 100 && valid_period >= 0);
        initialize_timeline(data, enable);
    } else {
        send_query(true);
    }
}

function ical_url(period, start, end, search) {
    var search_term = function(key, value) {
      return key + '/' + value + '/';
    };

    var url = '/events/';
    url += search_term('period', period);

    if (period === 'custom') {
      if (start) {
        url += search_term('start', start);
      }
      if (end) {
        url += search_term('end', end);
      }
    }

    if (search) {
      url += search_term('search', search);
    }

    url += 'ical/';

    return url;
}

function bind_events() {
    // Bind events
    // Update hash, on search input update.
    EventsLib.searchfield_elm.bind('propertychange keyup input paste', function(event) {
        hash_set_value('search', EventsLib.searchfield_elm.val());
    });

    EventsLib.period_selector_elm.change(function() {
        var period = EventsLib.period_selector_elm.val();
        hash_set_value('period', period);
        if (period === 'custom') {
            var start_date = EventsLib.datepicker_start_elm.datepicker('getDate');
            var end_date = EventsLib.datepicker_end_elm.datepicker('getDate');
            if (start_date) {
              hash_set_value('start', $.datepicker.formatDate('yy-mm-dd', start_date));
            }
            if (end_date) {
              hash_set_value('end', $.datepicker.formatDate('yy-mm-dd', end_date));
            }
        }
    });

    EventsLib.category_selector_elm.change(function() {
        hash_set_value('category', EventsLib.category_selector_elm.val());
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

    //set the suffix according to period
    var search_type = hash_get_value('period');
    var suffix = '';
    if (search_type === 'custom') {
        var start_date = hash_get_value('start');
        var end_date = hash_get_value('end');
        if (start_date && end_date) {
            suffix = ' for period ' + start_date + ' to ' + end_date;
        }
        else if (start_date) {
            suffix = ' from ' + start_date;
        }
        else if (end_date) {
            suffix = ' till ' + end_date;
        }
    }
    else if (search_type === 'future'){
        suffix = ' currently or in the future';
    }
    else if (search_type === 'past'){
        suffix = ' in the past';
    }

    if (number_of_events === 0) {
        EventsLib.events_table_elm.hide();
        EventsLib.events_number_elm.html('Sorry, no events found' + suffix + '.');
    }
    else {
        EventsLib.events_table_elm.show();

        if (number_of_events === 1) {
            EventsLib.events_number_elm.html('1 event found' + suffix + '.');
        }
        else {
            EventsLib.events_number_elm.html(number_of_events + ' events found' + suffix + '.');
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

    if ((parseInt(data.meta.limit, 10) === 0) ||
        (parseInt(data.meta.offset, 10) + EventsLib.results_batch >= parseInt(data.meta.total_count, 10))) {
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

    // Check if query result has less than 100 events
    // and period is either 'custom' or 'future'

    var period = hash_get_value('period');
    var valid_period = $.inArray(period, ['custom', 'future']);
    var enable = (parseInt(data.meta.total_count, 10)<100 && valid_period>=0);

    initialize_timeline(data, enable);

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

function LocalDateString(d){
    return (d.getFullYear() + '-' +
            pad2(d.getMonth() + 1) + '-' +
            pad2(d.getDate()));
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
    var start_date = undefined;
    var end_date = undefined;

    var start = hash_get_value('start');
    var end = hash_get_value('end');

    if (period === 'future') {
        start_date = new Date();
    }
    if (period === 'past') {
        end_date = new Date();
    }
    if (period !== 'custom') {
        if (start) {
          hash_set_value('start', '');
        }
        if (end) {
          hash_set_value('end', '');
        }
    }

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
        else if (period === 'custom') {
            if (start) {
                EventsLib.datepicker_start_elm.datepicker('setDate', start);
            }
            if (end) {
                EventsLib.datepicker_end_elm.datepicker('setDate', end);
            }

            start_date = EventsLib.datepicker_start_elm.datepicker('getDate');
            end_date = EventsLib.datepicker_end_elm.datepicker('getDate');

            extra_q += '&limit=0';

            if (start_date) {
                var start_utc_string = LocalDateString(start_date);
                extra_q += '&start__gte=' + start_utc_string;
            }

            if (end_date) {
                var end_utc_string = LocalDateString(end_date);
                extra_q += '&end__lte=' + end_utc_string;
            }
        }

        EventsLib.datepicker_start_elm.datepicker('setDate', start_date);
        EventsLib.datepicker_end_elm.datepicker('setDate', end_date);
    }

    // Search term.
    var search = hash_get_value('search');
    EventsLib.searchfield_elm.val(search);
    if (search) {
        extra_q += '&query=' + search;
    }

    // Update iCAL url
    EventsLib.multi_e_ical_elm.attr('href', ical_url(period, start, end, search));

    var category = hash_get_value('category');
    set_dropdown_value(EventsLib.category_selector_elm, category);
    if (category) {
        extra_q += '&categories__name__iexact=' + category;
    }

    if (period === 'custom' || category) {
        EventsLib.adv_search_elm.show();
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

    EventsLib.event_timeline_elm.hide();

    $('#events-map-button').click(function (e) {
        e.preventDefault();
        EventsLib.event_timeline_elm.fadeOut('fast');
        $('#map').fadeIn('slow');

        $(this).parent().addClass('active');
        $('#events-timeline-button').parent().removeClass('active');
    });

    $('#events-timeline-button').click(function (e) {
        e.preventDefault();
        $('#map').fadeOut('fast');
        EventsLib.event_timeline_elm.empty().show();
        show_timeline();
        $(this).parent().addClass('active');
        $('#events-map-button').parent().removeClass('active');
    });

    initialize_map();

    // Click geolocation button on load
    $('a[title="Show me where I am"]', '#map')[0].click();

    EventsLib.searchform_elm.submit(function (event) {
        event.preventDefault();
    });

    var period = hash_get_value('period');
    if (!period) {
        period = 'future';
        hash_set_value('period', period);
    }

    // Advanced button click.
    EventsLib.adv_search_icon_elm.click(function() {
        var visible = EventsLib.adv_search_elm.is(':visible');
        EventsLib.adv_search_elm.slideToggle();
    });

    //Initiate datepicker
    EventsLib.datepicker_elm.datepicker({
        onSelect: function(selectedDate) {
            var period = hash_get_value('period');

            if (period !== 'custom') {
                hash_set_value('period', 'custom');
            }

            if (this.id == 'date-start') {
                if (EventsLib.datepicker_start_elm.val() === '') {
                  hash_set_value('start', '');
                }
                else{
                  hash_set_value('start', selectedDate);
                }
            }

            if (this.id == 'date-end') {
                if (EventsLib.datepicker_end_elm.val() === '') {
                  hash_set_value('end', '');
                }
                else{
                  hash_set_value('end', selectedDate);
                }
            }

            send_query(newquery=true);
        },
        dateFormat: 'yy-mm-dd'
    });

    EventsLib.datepicker_elm.click(function(){
        $(this).datepicker('show');
    });

    var start_date = hash_get_value('start');
    var end_date = hash_get_value('end');

    if (start_date) {
        EventsLib.datepicker_start_elm.datepicker('setDate', start_date);
    }
    if (end_date) {
        EventsLib.datepicker_end_elm.datepicker('setDate', end_date);
    }

    // Set values to fields.
    set_dropdown_value(EventsLib.period_selector_elm, period);
    set_dropdown_value(EventsLib.category_selector_elm, hash_get_value('category'));

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
