$(document).ready(function() {

    var CLOUDMADE_API_KEY = $('body').data('cloudmade-api-key');
    var map;

    function initMap () {

        var cloudmade, center;

        if (!map) {
            map = new L.Map('map_point', { minZoom: 1 });
            cloudmade = new L.TileLayer(('https://ssl_tiles.cloudmade.com/' +
                                         CLOUDMADE_API_KEY +
                                         '/997/256/{z}/{x}/{y}.png'), { maxZoom: 18 });
            center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
            map.setView(center, 1).addLayer(cloudmade);

            // Update modal's LatLon fields.
            map.on('click', function(event) {
                $('#lat-temp').val(event.latlng.lat);
                $('#lon-temp').val(event.latlng.lng);
            });

            // Clicking "Use those" closes the modal and updates the hidden input fields.
            $('.use-these').click(function () {
                $('#lat').val($('#lat-temp').val());
                $('#lon').val($('#lon-temp').val());
            });
        }
    }

    // due to Foundation 4, we need to only draw the map once shown
    if ($.isFunction($.fn.foundation)) {
        $('#map-point').foundation('reveal', {
            opened: function () {
                //callback fires for any reveal on page so must check the modal id
                if (this.id === 'map-point') {
                     initMap();
                }
            }
        });
    } else {
        // For Foundation 2 we can draw on DOM ready
        initMap();
    }
});
