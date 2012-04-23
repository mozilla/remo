var qs;
var markers_array = [];
var map;

function initialize_map() {
    // Initialize map.
    map = new L.Map('map');
    attribution = ('Map data &copy; <a href="http://openstreetmap.org">' +
                   'OpenStreetMap</a> contributors, <a href="http://creativecommons.org/' +
                   'licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © ' +
                   '<a href="http://cloudmade.com">CloudMade</a>')
    cloudmade = new L.TileLayer('http://{s}.tile.cloudmade.com/' +
                                'b465ca1b6fe040dba7eec0291ecb7a8c/' +
                                '997/256/{z}/{x}/{y}.png',
                                { attribution: attribution, maxZoom: 18 });
    center = new L.LatLng(25, 0); // geographical point (longitude and latitude)
    map.setView(center, 2).addLayer(cloudmade);

    // When user clicks on map and a search filter exists, remove filter.
    map.on('click', function(e) {
        var val = $('input#searchfield').val();
        if (val != '') {
            search_string = '';
            $('input#searchfield').val(search_string);
            qs.search(search_string);
            qs.cache();
            redraw_grid();
        }
    });
}


function add_pointers() {
    // Add user pointers on map.
    $('.profiles-li-item').each(function(index, item) {
        lat = $(item).data('lat');
        lon = $(item).data('lon');
        var markerLocation = new L.LatLng(lat, lon);
        var marker = new L.Marker(markerLocation);

        // Clicking on a pointer makes others disappear if visible, or
        // otherwise appear.
        marker.on('click', function(e) {
            var val = $('input#searchfield').val();
            var fullname = $(item).data('fullname');
            if (val != '') {
                search_string = '';
            }
            else {
                search_string = fullname;
            }
            $('input#searchfield').val(search_string);
            qs.search(search_string)
            qs.cache();
            redraw_grid();
        })

        map.addLayer(marker);
        markers_array[item.id] = marker;
    })
}


function redraw_grid() {
    // Redraw Reps grid.
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

function calculate_number_of_reps() {
    // Count and display the number of visible reps.
    number_of_reps = $(".profiles-li-item[style!='display: none;']").length
    $("#profiles-number-of-reps").html(number_of_reps);
}

$(document).ready(function () {
    initialize_map();
    add_pointers();

    $('#searchform').submit(function (event) {
        event.preventDefault();
    });

    $('#listviewbutton').bind('click', function () {
        $('#profiles_listview').hide();
        $('#profiles_gridview').show();
        redraw_grid();
    });

    $('#gridviewbutton').bind('click', function () {
        $('#profiles_gridview').hide();
        $('#profiles_listview').show();
    });

    qs = $('input#searchfield').quicksearch('ul#searchlist li', {
        'show': function () {
            map.addLayer(markers_array[this.id]);
            $('#tr' + this.id.slice(2)).show();
            $(this).show();
        },
        'hide': function () {
            map.removeLayer(markers_array[this.id]);
            $('#tr' + this.id.slice(2)).hide();
            $(this).hide();
        },
        'onAfter': function () {
            redraw_grid();
            calculate_number_of_reps();
        }
    });

    search_string = window.location.pathname.substr(8);
    search_string = unescape(search_string);
    if (search_string.length > 0) {
        $('input#searchfield').val(search_string);
        qs.search(search_string);
        qs.cache();
        redraw_grid();
    }
});
