var markers_array = [];

/* Creation of map object */
var map = new OpenLayers.Map("map");

/* Declaring base layer */
var osm = new OpenLayers.Layer.OSM();

/* Adding layer to map */
map.addLayer(osm);

/* Zooming inital to extend */
map.zoomToMaxExtent();

/* Centering and zooming to fit global view */
map.setCenter(new OpenLayers.LonLat(0, 10), 2);
map.zoomToMaxExtent();
map.setCenter(new OpenLayers.LonLat(0, 15).transform(
    new OpenLayers.Projection("EPSG:4326"),
    new OpenLayers.Projection("EPSG:900913")
), 2);

/* initialize markers overlay */
var markers = new OpenLayers.Layer.Markers("Reps");
map.addLayer(markers);
var size = new OpenLayers.Size(21, 33);
var offset = new OpenLayers.Pixel(-(size.w / 2), -size.h);
var icon = new OpenLayers.Icon('/media/img/remo/marker.png', size, offset);
markers.setOpacity(0.7);

function redraw_grid() {
    // Due to a bug in internet explorer we have to set clear:left css
    // attribute on some block-grid 's. Update each block to ensure that
    // only the leftest visible blocks get the extra attribute.
    $('.block-grid.two-up>li').css({'clear': ''});
    $('.block-grid.three-up>li').css({'clear': ''});
    $('.block-grid.four-up>li').css({'clear': ''});
    $('.block-grid.five-up>li').css({'clear': ''});

    $('.block-grid.two-up>li:visible').filter(
        function (index) {return index % 2 == 0;}).css('clear', 'left')
    $('.block-grid.three-up>li:visible').filter(
        function (index) {return index % 3 == 0;}).css('clear', 'left')
    $('.block-grid.four-up>li:visible').filter(
        function (index) {return index % 4 == 0;}).css('clear', 'left')
    $('.block-grid.five-up>li:visible').filter(
        function (index) {return index % 5 == 0;}).css('clear', 'left')
}

$(function () {
    $('#searchform').submit(function (event) {
        event.preventDefault();
    });

    $('#listviewbutton').bind('click', function () {
        $('#profiles_listview').hide();
        $('#profiles_gridview').show();
        qs.cache();
    });

    $('#gridviewbutton').bind('click', function () {
        $('#profiles_gridview').hide();
        $('#profiles_listview').show();
        qs1.cache();
    });

    var qs = $('input#searchfield').quicksearch('ul#searchlist li', {
        'show': function () {
            markers_array[$(this).attr('id')].display(true);
            $(this).show();
        },
        'hide': function () {
            markers_array[$(this).attr('id')].display(false);
            $(this).hide();
        },
        'onAfter': function () {
            redraw_grid();
        }
    });

    qs1 = $('input#searchfield').quicksearch('table#list-people-view tbody tr');

    search_string = window.location.pathname.substr(8);
    search_string = unescape(search_string);
    if (search_string.length > 0) {
        $('input#searchfield').val(search_string);
        qs.cache();
    }
});
