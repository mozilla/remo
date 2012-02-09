var markers_array = new Array();

/* Creation of map object */
var map = new OpenLayers.Map("map");

/* Declaring base layer */
var osm = new OpenLayers.Layer.OSM();

/* Adding layer to map */
map.addLayer(osm);

/* Zooming inital to extend */
map.zoomToMaxExtent();

/* Centering and zooming to fit global view */
map.setCenter(new OpenLayers.LonLat(0,10), 2);
map.zoomToMaxExtent();
map.setCenter(new OpenLayers.LonLat(0,15).transform(
    new OpenLayers.Projection("EPSG:4326"),
    new OpenLayers.Projection("EPSG:900913")
), 2);

/* initialize markers overlay */
var markers = new OpenLayers.Layer.Markers("Reps");
map.addLayer(markers);
var size = new OpenLayers.Size(21, 33);
var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
var icon = new OpenLayers.Icon('/media/img/remo/marker.png',size,offset);
markers.setOpacity(0.7);


$(function() {
    $('#searchform').submit(function(event) {
	event.preventDefault();
    })

    $('#listviewbutton').bind('click', (function() {
	$('#profiles_listview').hide();
	$('#profiles_gridview').show();
	qs.cache();
    }))

    $('#gridviewbutton').bind('click', (function() {
	$('#profiles_gridview').hide();
	$('#profiles_listview').show();
	qs1.cache();
    }))

    var qs = $('input#searchfield').quicksearch('ul#searchlist li', {
	'show': function () {
	    markers_array[$(this).attr('id')].display(true);
	    $(this).show();
	},
	'hide': function () {
	    markers_array[$(this).attr('id')].display(false);
	    $(this).hide();
	}
    })
    var qs1 = $('input#searchfield').quicksearch('table#list-people-view tr td', {
	'show': function () {
	    markers_array[$(this).attr('id')].display(true);
	    $(this).show();
	},
	'hide': function () {
	    markers_array[$(this).attr('id')].display(false);
	    $(this).hide();
	}
    })

    search_string = window.location.pathname.substr(8);
    if (search_string.length > 0) {
	$('input#searchfield').val(search_string);
	qs.cache();
    }
});
