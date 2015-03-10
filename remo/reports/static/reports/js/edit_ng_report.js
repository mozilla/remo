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

        geocoder.reverseQuery([lon,lat], function (e, data) {
            if (e || data.results.length < 1) {
                $input.val(lat + ', ' + lon);
                return false;
            }
            $.each(data.results[0], function (index, value) {
                array.push(value.name);
            });
            if (array.length > 0) {
                $input.val(array.join(', '));
            }
            else {
                $input.val(lat + ', ' + lon);
            }
        });
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

        // once the user selects a location
        // make the field user editable
        $('#id_location').removeAttr('readonly');
    });

    // set date picker defaults
    initDatePicker();

})(jQuery);
