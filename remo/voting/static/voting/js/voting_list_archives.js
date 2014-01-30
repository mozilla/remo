$(document).ready(function () {
    'use strict';
    // Apply prettyDate on all elements with data-time attribute.
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC: true});
    paginatorSelector();
});
