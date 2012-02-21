$(document).ready( function () {
    var map = new OpenLayers.Map('map', {
        controls: [
            new OpenLayers.Control.Navigation(),
            new OpenLayers.Control.ArgParser(),
            new OpenLayers.Control.Attribution()],
        projection: new OpenLayers.Projection('EPSG:900913')
    });
    var panel = new OpenLayers.Control.Panel();
    var markers = new OpenLayers.Layer.Markers('Reps');
    var osm = new OpenLayers.Layer.OSM();

    map.addLayers([osm]);
    map.zoomToMaxExtent();
    map.addLayer(markers);

    var map_el = $('#map');
    var lonlat = new OpenLayers.LonLat(map_el.data('lon'),
                                       map_el.data('lat'));
    map.setCenter(lonlat, 8); // Zoom level
    var size = new OpenLayers.Size(21, 33);
    var offset = new OpenLayers.Pixel(-(size.w / 2), -size.h);
    var icon = new OpenLayers.Icon(map_el.data('mediaurl') +
                                   'img/remo/marker.png', size, offset);
    markers.addMarker(new OpenLayers.Marker(lonlat, icon.clone()));
    markers.setOpacity(0.7);
})
