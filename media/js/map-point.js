OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
    defaultHandlerOptions: {
        'single': true,
        'double': false,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
    },

    initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {}, this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
            this, arguments
        );
        this.handler = new OpenLayers.Handler.Click(
            this, {
                'click': this.trigger
            }, this.handlerOptions
        );
    },

    trigger: function(e) {
        var lonlat = map.getLonLatFromViewPortPx(e.xy);
        $('input.point-lat-temp').val(Math.round(((lonlat.lat/100000)*1000000))/1000000);
        $('input.point-long-temp').val(Math.round(((lonlat.lon/100000)*1000000))/1000000);
    }

});
var map;

map = new OpenLayers.Map('map');

var osm = new OpenLayers.Layer.OSM();

map.addLayers([osm]);

map.zoomToMaxExtent();

var click = new OpenLayers.Control.Click();
map.addControl(click);
click.activate();

//Clicking "Use those" closes the modal and updates the hidden input fields
$('.use-those').click(function() {
  $('input.point-lat').val($('input.point-lat-temp').val());
  $('input.point-long').val($('input.point-long-temp').val());
});
