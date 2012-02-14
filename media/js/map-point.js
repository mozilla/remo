OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
    defaultHandlerOptions: {
        'single': true,
        'double': false,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
    },

    initialize: function (options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {},
            this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
            this,
            arguments
        );
        this.handler = new OpenLayers.Handler.Click(
            this,
            {
                'click': this.trigger
            },
            this.handlerOptions
        );
    },

    trigger: function (e) {
        var lonlat = map_point.getLonLatFromViewPortPx(e.xy);
        $('input.point-lat-temp').val(lonlat.lat);
        $('input.point-long-temp').val(lonlat.lon);
    }

});

var map_point;

map_point = new OpenLayers.Map('map_point', {
    projection: new OpenLayers.Projection("EPSG:900913")
} );

var osm = new OpenLayers.Layer.OSM();

map_point.addLayers([osm]);

map_point.zoomToMaxExtent();

var click = new OpenLayers.Control.Click();
map_point.addControl(click);
click.activate();

//Clicking "Use those" closes the modal and updates the hidden input fields
$('.use-those').click(function () {
    $('input.point-lat').val($('input.point-lat-temp').val());
    $('input.point-long').val($('input.point-long-temp').val());
});

