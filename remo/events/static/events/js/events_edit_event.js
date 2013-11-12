$(document).ready(function() {
    'use strict';

    var MAPBOX_TOKEN = $('body').data('mapbox-token');

    // Move foundation elements to position.
    ['start', 'end'].forEach(function(obj) {
        ['0_month', '0_day', '0_year', '1_hour', '1_minute'].forEach(function(elem) {
            var destination = $('#' + obj + '-' + elem.substr(2));
            var form_elem = $('#id_' + obj + '_form_' + elem);
            var foundation_elem = form_elem.next().detach();

            form_elem.detach().appendTo(destination);
            foundation_elem.appendTo(destination);
        });
    });

    // Auto change end year, month, day when start changes.
    ['month', 'day', 'year'].forEach(function(when) {
        $('#id_start_form_0_' + when).change(function() {
            var obj = $('#id_end_form_0_' + when);
            obj.val($('#id_start_form_0_' + when).val());
            obj.trigger('change');
        });
    });

    // Dynamically add Metric forms
    $('form').on('click', '#events-add-metric-button', append_to_formset);
    $('.use-these').on('selected', function() {
        // Use reverse geocoding to prepopulate fields
        var geocoder = new L.mapbox.geocoder(MAPBOX_TOKEN);
        var lat = $('#lat').val();
        var lon = $('#lon').val();
        var latlng = [parseFloat(lon), parseFloat(lat)];
        geocoder.reverseQuery(latlng, function(error, data) {

            function selectType(results, type) {
                for (var i in results) {
                    if (results[i].type === type) {
                        return results[i].name;
                    }
                }
            }

            if (data.results.length > 0) {
                // Select first result
                var result = data.results[0];
                var city = selectType(result, 'place') || selectType(result, 'city');
                var province = selectType(result, 'province');
                var country = selectType(result, 'country');

                var country_field = $('#id_country');
                var country_query = country_field.children('option[value="' + country + '"]');
                var country_default = country_field.children('option[value=""]');

                if (country_query.length) {
                    country_query.prop('selected', true);
                }
                else {
                    country_default.prop('selected', true);
                }

                $(country_field).prop('selected', true);
                $('#id_city').val(city);
                $('#id_region').val(province);
            }
        });
    });
});
