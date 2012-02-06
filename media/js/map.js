
/* Creation of map object */
var map = new OpenLayers.Map("map");

/* Declaring base layer */
var osm = new OpenLayers.Layer.OSM();

/* Adding layer to map */
map.addLayers([osm]);

/* Zooming inital to extend */
map.zoomToMaxExtent();

/* Centering and zooming to fit global view */
map.setCenter(new OpenLayers.LonLat(0,10), 2);
