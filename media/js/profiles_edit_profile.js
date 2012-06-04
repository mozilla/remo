$(document).ready(function() {
    var map = new L.Map('map_point', { minZoom: 1 });
    var cloudmade = new L.TileLayer(('http://{s}.tile.cloudmade.com/' +
                                     'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                     '997/256/{z}/{x}/{y}.png'), { maxZoom: 18 });
    var center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    map.setView(center, 1).addLayer(cloudmade);

    // Update modal's LatLon fields.
    map.on('click', function(event) {
        $('input.point-lat-temp').val(event.latlng.lat);
        $('input.point-long-temp').val(event.latlng.lng);
    });

    // Clicking "Use those" closes the modal and updates the hidden input fields.
    $('.use-these').click(function () {
        $('input.point-lat').val($('input.point-lat-temp').val());
        $('input.point-long').val($('input.point-long-temp').val());
    });
});
