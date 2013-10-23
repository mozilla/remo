$(document).ready(function() {
    'use strict';
    $('#page-select').on('change', function() {
        window.location = $(this).val();
    });
});
