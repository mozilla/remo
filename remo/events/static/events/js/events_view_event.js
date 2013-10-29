var CLOUDMADE_API_KEY = $('body').data('cloudmade-api-key');

function initialize_map() {
    // Initialize map.
    var map = new L.Map('map', { minZoom: 1 });
    var cloudmade = new L.TileLayer('https://ssl_tiles.cloudmade.com/' +
                                    CLOUDMADE_API_KEY +
                                    '/997/256/{z}/{x}/{y}.png',
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

function set_tooltips() {
    // Set time tooltip to display the time to your browser's timezone.
    var title = '';
    var item = $('#datetime-tip');

    var user_start_date = new Date(item.data('date-start') + 'Z');
    var user_end_date = new Date(item.data('date-end') + 'Z');

    var start_date = new Date(item.data('date-local-start') + 'Z');
    var local_start_date = new Date(item.data('date-local-start') + 'Z');
    local_start_date.setHours(start_date.getHours(),
                              start_date.getMinutes() + start_date.getTimezoneOffset());

    var end_date = new Date(item.data('date-local-end') + 'Z');
    var local_end_date = new Date(item.data('date-local-end') + 'Z');
    local_end_date.setHours(end_date.getHours(),
                            end_date.getMinutes() + end_date.getTimezoneOffset());

    title = ('Event starts from ' +
             format_hour(local_start_date) +
             ' to ' +
             format_hour(local_end_date) +
             ' (local time) or ' +
             'from ' + format_hour(user_start_date) + ' to ' +
             format_hour(user_end_date) + ' (your time).');

    // We need to add title, add class and call tooltips() after we
    // have initialized the tooltip.
    item.attr('title', title);
    item.addClass('has-tip');
}

function initialize_mashup() {
    // Setup flickr and twitter mashups.
    //
    // We first fetch photos from flickr and randomize them, so on
    // each page load users see a different set of photos.
    //
    var flickr_mashup = $('#flickr-mashup');
    var tweet_mashup = $('#tweet-mashup');
    var hashtag = flickr_mashup.data('hashtag');
    if (hashtag) {
        flickr_mashup.flickrfeed('', flickr_mashup.data('hashtag').substr(1), {
            limit: 20,
            title: false,
            date: false,
            header: false,
            randomize: true
        }).bind('loaded', function() {
            // Check if images exist
            if ($('.flickrRow').length !== 0) {
                flickr_mashup.slideDown();
            }
        });

        tweet_mashup.tweet({
            query: tweet_mashup.data('hashtag'),
            page: 1,
            avatar_size: 32,
            count: 20,
            retweets: false
        }).bind('loaded', function() {
            var ul = $('ul.tweet_list');
            var li_elms = ul.find('li');

            // Filter out unofficial retweets
            var rt_regex = new RegExp('RT ');
            li_elms = $(li_elms).filter(function() {
                var match = rt_regex.test($(this).find('.tweet_text')[0].textContent);
                if (match) {
                    $(this).remove();
                    return true;
                }
                return false;
            });

            // If we have tweets.
            if (li_elms.length > 0) {
                $('#tweet-mashup-container').slideDown();

                ul.find('a').attr('target', '_blank');
                if (li_elms.length > 4) {
                    var ticker = function() {
                        setTimeout(function() {
                            ul.find('li:first').animate(
                                {marginLeft: '-305px'}, 500, function() {
                                    $(this).detach().appendTo(ul).removeAttr('style');
                                });
                            ticker();
                        }, 5000);
                    };
                    ticker();
                }
            }
        });
    }
}

$(document).ready(function() {
    set_tooltips();
    initialize_map();
    initialize_mashup();

    // Apply prettyDate on all elements with data-time attribute.
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC:true});
});
