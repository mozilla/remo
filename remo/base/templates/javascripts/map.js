
/* Creation of map object */
var map = new OpenLayers.Map("map");

/* Declaring base layer */
var ol_wms = new OpenLayers.Layer.WMS(
    "OpenLayers WMS",
    "http://vmap0.tiles.osgeo.org/wms/vmap0",
    {layers: "basic"}
);

/* Adding layer to map */
map.addLayers([ol_wms]);

/* Zooming inital to extend */
map.zoomToMaxExtent();

/* Centering and zooming to fit global view */
map.setCenter(new OpenLayers.LonLat(0,10), 2);