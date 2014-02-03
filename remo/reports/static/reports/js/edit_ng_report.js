(function($) {
    'use strict';

    var MAPBOX_ΤΟΚΕN = $('body').data('mapbox-token');

    /*
     * Performs a reverse geocode lookup
     * Params: @lon string, @lat string, $input object
     */
    function doReverseGeo (longitude, latitude, $input) {
        var geocoder = L.mapbox.geocoder(MAPBOX_ΤΟΚΕN);
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
        var triggerInput = $('#active-report-form').data('campaign-trigger');

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
     * Override map_modal.js click handler as reports template
     * uses different ID's for lat/lng form values.
     */
    $('.use-these').off().on('click', function () {
        var lat = $('#lat-temp').val();
        var lon = $('#lon-temp').val();

        $('#id_latitude').val(lat);
        $('#id_longitude').val(lon);

        doReverseGeo(lon, lat, $('#id_location'));
    });

    // Set campaign input visibility on select field change
    $('#id_activity').on('change', setCampaignPanel);
    // Set campaign panel visibility on page load
    setCampaignPanel();
    // set date picker defaults
    initDatePicker();

})(jQuery);
