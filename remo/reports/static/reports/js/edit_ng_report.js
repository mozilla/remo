(function($) {

    'use strict';

    var map;
    var MAPBOX_ΤΟΚΕN = $('body').data('mapbox-token');
    var geocoder = L.mapbox.geocoder(MAPBOX_ΤΟΚΕN);

    var $lon = $('#id_longitude');
    var $lat = $('#id_latitude');
    var $location = $('#id_location');

    var $lat_temp = $('#lat-temp');
    var $lon_temp = $('#lon-temp');

    function initMap () {
        var center;

        if (!map) {
            map = L.mapbox.map('map_point', MAPBOX_ΤΟΚΕN);
            center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
            map.setView(center, 1);

            // Update modal's LatLon fields.
            map.on('click', function(event) {
                $lat_temp.val(event.latlng.lat);
                $lon_temp.val(event.latlng.lng);
            });

            // Clicking "Use those" closes the modal and updates the hidden input fields.
            $('.use-these').on('click', function () {
                var lat = $lat_temp.val();
                var lon = $lon_temp.val();
                $lat.val(lat);
                $lon.val(lon);
                doReverseGeo(lon, lat, $location);
            });
        }
    }

    /*
     * Performs a reverse geocode lookup
     * Params: @lon string, @lat string, $input object
     */
    function doReverseGeo (longitude, latitude, $input) {
        var array = [];
        var lat = parseFloat(latitude);
        var lon = parseFloat(longitude);

        // first clear the location input field
        $input.val('');

        geocoder.reverseQuery([lon,lat], function (e, data) {
            if (data.results.length < 1 || e) {
                return false;
            }
            $.each(data.results[0], function (index, value) {
                array.push(value.name);
            });
            $input.val(array.join(', '));
        });
    }

    /*
     * Toggles the campaign input field if activity type is
     * "Participated in a campaign". Makes input a required field
     * when it is visible, removes input value when hidden.
     */
    function setCampaignPanel () {
        var text = $('select#id_activity').find(":selected").text();
        var $panel = $('#campaign-panel');
        var input = $panel.find('input');
        var triggerInput = 'Participated in a campaign';

        if (text === triggerInput) {
            $panel.slideDown();
            input.attr('required', 'required');
        } else {
            $panel.slideUp();
            input.val('');
            input.removeAttr('required');
        }
    }

    /*
     * Initialize date picker widget and set ISO date format
     * If the field is empty, pre-populate with current date
     */
    function initDatePicker () {
        var $input = $('input.datepicker');
        $input.datepicker({
            autoSize: true,
            dateFormat: 'dd MM yy'
        });

        if ($input.val() === '') {
            $input.datepicker('setDate', Date.now());
        }
        else {
            var date = $.datepicker.parseDate("yy-mm-dd", $input.val());
            $input.datepicker('setDate', date);
        }
    }

    /*
     * Set default values and bind form events
     */
    // Set campaign input visibility on select field change
    $('#id_activity').on('change', setCampaignPanel);
    // Set campaign panel visibility on page load
    setCampaignPanel();

    // Open map modal when user clicks the location button
    $('#map-point').foundation('reveal', {
        opened: function () {
            //callback fires for any reveal on page so must check the modal id
            if (this.id === 'map-point') {
                initMap();
            }
        }
    });

    // Perform initial reverse lookup for contribution location
    // if location field is empty, and we have geo-coordinates
    // from the rep's profile
    if ($lon.val() !== '' && $lat.val() !== '' && $location.val() === '') {
        doReverseGeo($lon.val(), $lat.val(), $location);
    }
    // set date picker defaults
    initDatePicker();

})(jQuery);
