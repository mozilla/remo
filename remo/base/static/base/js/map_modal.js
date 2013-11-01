$(document).ready(function() {

    var MAPBOX_TOKEN = $('body').data('mapbox-token');
    var map;

    function initMap () {

        var center;

        if (!map) {
            center = new L.LatLng(25, 0);
            map = new L.mapbox.map('map_point', MAPBOX_TOKEN, {minZoom: 1});
            map.setView(center, 1);

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

    $('#map-point').foundation('reveal', {
        opened: function () {
            //callback fires for any reveal on page so must check the modal id
            if (this.id === 'map-point') {
                 initMap();
            }
        }
    });
});
