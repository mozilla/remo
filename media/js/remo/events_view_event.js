function initialize_map() {
    // Initialize map.
    var map = new L.Map('map', { minZoom: 1 });
    var cloudmade = new L.TileLayer('http://{s}.tile.cloudmade.com/' +
                                    'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                    '997/256/{z}/{x}/{y}.png',
                                    { attribution: '', maxZoom: 18 });
    var map_elm = $('#map');
    var lat = map_elm.data('lat');
    var lon = map_elm.data('lon');
    var markerLocation = new L.LatLng(lat, lon);
    var marker = new L.Marker(markerLocation, { clickable: false });
    var center = new L.LatLng(lat, lon); // geographical point (longitude and latitude)
    map.setView(center, 15);
    map.addLayer(cloudmade);
    map.addLayer(marker);
}

function pad2(number) {
    // Pad numbers
    // snippet from
    // http://www.electrictoolbox.com/pad-number-two-digits-javascript/
    return (number < 10 ? '0' : '') + number;
}

function format_hour(date_obj) {
    // Format date_obj to HH:MM.
    return pad2(date_obj.getHours()) + ':' + pad2(date_obj.getMinutes());
}

function set_time_tooltip() {
    // Set time tooltip to display the time to your browser's timezone.
    var title = '';
    var item = $('#datetime-tip');

    var start_date = new Date(item.data('date-start'));
    var user_start_date = new Date(item.data('date-start'));
    user_start_date.setHours(start_date.getHours(),
                             start_date.getMinutes() - start_date.getTimezoneOffset());
    var end_date = new Date(item.data('date-end'));
    var user_end_date = new Date(item.data('date-end'));
    user_end_date.setHours(end_date.getHours(),
                           end_date.getMinutes() - end_date.getTimezoneOffset());

    if (item.data('is-multidate')) {
        var local_start_date = new Date(item.data('date-local-start'));
        var local_end_date = new Date(item.data('date-local-end'));

        title = ('Event starts daily at ' +
                 format_hour(local_start_date) +
                 ' and ends ' +
                 format_hour(local_end_date) +
                 ' local time. ' +
                 'That\'s ' + format_hour(user_start_date) + ' - ' +
                 format_hour(user_end_date) + ' yours.');
    }
    else {
        title = ('That\'s local times.<br/>Your time:<br/>' +
                 format_hour(user_start_date) +
                 ' - ' +
                 format_hour(user_end_date) +
                 '<br/>on ' + user_start_date.toDateString());
    }

    // We need to add title, add class and call tooltips() after we
    // have initialized the tooltip.
    item.attr('title', title);
    item.addClass('has-tip');
    $(document).tooltips();
}

function initialize_mashup() {
    // Setup flickr and twitter mashups.
    //
    // We first fetch photos from flickr and randomize them, so on
    // each page load users see a different set of photos. If we have
    // photos we also try to load related tweets.
    //
    var flickr_mashup = $('#flickr-mashup');
    flickr_mashup.flickrfeed('', flickr_mashup.data('hashtag').substr(1), {
        limit: 20,
        title: false,
        date: false,
        header: false,
        randomize: true
    }).bind('loaded', function() {
        // Check if images exist
        if ($('.flickrRow').length === 0) {
            // No images, don't display tweets either.
            return;
        }
        flickr_mashup.show();

        $('#tweet-mashup').tweet({
            query: $('#tweet-mashup').data('hashtag'),
            page: 1,
            avatar_size: 32,
            count: 20,
            loading_text: 'fetching tweets ...'
        }).bind('loaded', function() {
            var ul = $('ul.tweet_list');

            // If we have tweets.
            if (ul.find('li').length > 0) {
                $('#tweet-mashup-container').show();
                $('#tweet-mashup-fade').show();

                ul.find('a').attr('target', '_blank');
                var ticker = function() {
                    setTimeout(function() {
                        ul.find('li:first').animate( {marginTop: '-4em'}, 500, function() {
                            $(this).detach().appendTo(ul).removeAttr('style');
                        });
                        ticker();
                    }, 5000);
                };
                ticker();
            }
        });
    });
}

$(document).ready(function() {
    set_time_tooltip();
    initialize_map();
    initialize_mashup();
});
