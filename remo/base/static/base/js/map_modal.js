$(document).ready(function() {
    'use strict';

    var MAPBOX_TOKEN = $('body').data('mapbox-token');
    var map;

    function handleLocationFound(e) {
        // setView and zoom map when geolocation succeeds
        this.setView(e.latlng, 10);
        $('#lat-temp').val(e.latlng.lat);
        $('#lon-temp').val(e.latlng.lng);
    }

    function handleLocationError() {
        // Show message when geolocation fails
        var msg = 'Sorry, we could not determine your location.';
        showMessage({
            'msg': msg,
            'tag': 'warning',
            'id': '#map-message-container',
            'replace': true,
            'hide': true
        });
    }

    function initMap () {

        var center;

        if (!map) {

            map = new L.mapbox.map('map_point', MAPBOX_TOKEN, {minZoom: 1});
            addAttributionOSM(map);

            var lat = $('#map_point').data('lat');
            var lng = $('#map_point').data('lon');

            L.control.locate({
                setView: false,
                onLocationError: handleLocationError,
                locateOptions: {
                    watch: false
                }
            }).addTo(map);

            map.on('locationfound', handleLocationFound);

            if (lat && lng) {
                // Same zoom-level as in events list
                center = new L.LatLng(lat, lng);
                map.setView(center, 5);
            }
            else {
                // Fallback if no lat-lon defined
                center = new L.LatLng(25, 0);
                map.setView(center, 1);
            }

            $('#lat-temp').val(center.lat);
            $('#lon-temp').val(center.lng);

            var control = L.mapbox.geocoderControl(MAPBOX_TOKEN).addTo(map);

            control.on('found', function(response) {
                if (response.results.length == 1) {
                    var latlng = map.getCenter();
                    $('#lat-temp').val(latlng.lat);
                    $('#lon-temp').val(latlng.lng);
                }
                else {
                    $('.leaflet-control-mapbox-geocoder-results > a').click(function(event) {
                        var latlng = map.getCenter();
                        $('#lat-temp').val(latlng.lat);
                        $('#lon-temp').val(latlng.lng);
                    });
                }
            });

            control.on('error', function(result) {
                var query = result.target._input.value;
                var msg = 'Sorry, no results found for search term: ' + query;
                showMessage({
                    'msg': msg,
                    'tag': 'error',
                    'id': '#map-message-container',
                    'replace': true,
                    'hide': true
                });
            });

            // Update modal's LatLon fields.
            map.on('click', function(event) {
                $('#lat-temp').val(event.latlng.lat);
                $('#lon-temp').val(event.latlng.lng);
            });

            // Clicking "Use those" closes the modal and updates the hidden input fields.
            $('.use-these').click(function () {
                var lat = $('#lat-temp').val();
                var lon = $('#lon-temp').val();

                $('#lat').val(lat);
                $('#lon').val(lon);
                $(this).trigger('selected');
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
