/**
 * Plugin: jquery.zFlickrFeed
 *
 * Version: 1.0.2
 * (c) Copyright 2011, Zazar Ltd
 *
 * Description: jQuery plugin for display of Flickr photo feeds
 *
 * History:
 * 1.0.2 - Fixed date option when not displaying
 * 1.0.1 - Corrected issue with multiple instances
 *
 * Modified by Giorgos Logiotatidis <seadog@sealabs.net> for
 * reps.mozilla.org
 *
 **/

(function($){
    $.fn.flickrfeed = function(userid, tags, options) {
        // Set pluign defaults
        var defaults = {
            limit: 10,
            header: true,
            imagesize: 'small',
            titletag: 'h4',
            title: true,
            date: true,
            randomize: false
        };
        options = $.extend(defaults, options);

        // Remove any prepending #
        tags = tags.replace('/^#/', '');

        // Functions
        return this.each(function(i, e) {
            var $e = $(e);

            // Add feed class to user div
            if (!$e.hasClass('flickrFeed')) $e.addClass('flickrFeed');

            // Define Flickr feed API address
            var api = 'http://api.flickr.com/services/feeds/photos_public.gne?lang=en-us&format=json&jsoncallback=?';
            if (userid !== '') api += '&id=' + userid;
            if (tags !== '') api += '&tags=' + tags;

            // Send request
            $.getJSON(api, function(data){

                // Process the feeds
                _callback(e, data, options);
            });
        });
    };

    // Callback function to create HTML result
    var _callback = function(e, data, options) {
        if (!data) {
            return false;
        }
        var html = '';
        var row = 'odd';
        var desc = data.title;

        // Add header if required
        if (options.header) {
            desc = data.description;

            html += '<div class="flickrHeader">' +
                '<a href="'+ data.link +'" title="'+ desc +'">'+ data.title +'</a>' +
                '</div>';
        }

        // Add body
        html += '<div class="flickrBody">' + '<ul>';

        var feeds = data.items;
        var count = feeds.length;
        if (count > options.limit) count = options.limit;

        // Pseudo randomize array
        if (options.randomize) {
            feeds = feeds.sort(function() { return 0.5 - Math.random();});
        }

        // Add feeds
        for (var i=0; i<count; i++) {

            // Get individual feed
            var photo= feeds[i];
            var link = '<a target="_blank" href="'+ photo.link + '">';

            // Add feed row
            html += '<li class="flickrRow '+ row +'">';

            // Select image size
            var src = photo.media.m;
            if (options.imagesize == 'square') src = src.replace('_m', '_s');
            if (options.imagesize == 'thumbnail') src = src.replace('_m', '_t');
            if (options.imagesize == 'medium') src = src.replace('_m', '');

            html += link +'<img src="'+ src +'"></a>';

            // Add title if required
            if (options.title) html += '<'+ options.titletag +'>'+ photo.title +'</'+ options.titletag +'>';

            // Add date if required
            if (options.date) {
                var photoDate = new Date(photo.date_taken);
                photoDate = photoDate.toLocaleDateString() + ' ' + photoDate.toLocaleTimeString();
                html += '<div>'+ photoDate +'</div>';
            }

            html += '</li>';

            // Alternate row classes
            if (row == 'odd') {
                row = 'even';
            } else {
                row = 'odd';
            }
        }

        html += '</ul>' + '</div>';

        $(e).html(html);
        $(e).trigger('loaded');
    };
})(jQuery);
