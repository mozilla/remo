$(document).ready(function () {
    'use strict';

    // Dashboard buttons
    var $reps_grid_button = $('.dashboard-mozillians-reps-grid-button');
    var $reps_reports_button = $('.dashboard-mozillians-reps-reports-button');
    var $event_future_button = $('.dashboard-events-future-button');
    var $events_past_button = $('.dashboard-events-past-button');

    // Dashboard block containers
    var $reps_grid_block = $('.dashboard-mozillians-reps-grid-block');
    var $reps_reports_block = $('.dashboard-mozillians-reps-reports-block');
    var $events_future_block = $('.dashboard-events-future-block');
    var $events_past_block = $('.dashboard-events-past-block');

    $reps_grid_button.on('click', function (e) {
        e.preventDefault();
        $reps_grid_block.removeClass('hidden');
        $reps_reports_block.addClass('hidden');
        $reps_grid_button.parent().addClass('active');
        $reps_grid_button.parent().siblings().removeClass('active');
    });

    $reps_reports_button.on('click', function (e) {
        e.preventDefault();
        $reps_reports_block.removeClass('hidden');
        $reps_grid_block.addClass('hidden');
        $reps_reports_button.parent().addClass('active');
        $reps_reports_button.parent().siblings().removeClass('active');
    });

    $event_future_button.on('click', function (e) {
        e.preventDefault();
        $events_future_block.removeClass('hidden');
        $events_past_block.addClass('hidden');
        $event_future_button.parent().addClass('active');
        $event_future_button.parent().siblings().removeClass('active');
    });

    $events_past_button.on('click', function (e) {
        e.preventDefault();
        $events_past_block.removeClass('hidden');
        $events_future_block.addClass('hidden');
        $events_past_button.parent().addClass('active');
        $events_past_button.parent().siblings().removeClass('active');
    });

    $('table').each(function(index, item) { $(item).stupidtable(); });
    // Apply prettyDate on all elements with data-time attribute.
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC:true});

    $("button[data-reveal-id='mail-reps-modal']").on('click', function () {
        var area_id = $('.dashboard-tabs-labels a.active').data('id');
        $('input[name=functional_area]').val(area_id);
    });

    $('.dashboard-tabs-labels a').on('click', function (e) {
        e.preventDefault();
        $('.dashboard-tabs-labels a.active').removeClass('active');
        $('.dashboard-tabs .content.active').removeClass('active');
        $(this.hash + 'Tab').addClass('active');
        $(this).addClass('active');
    });
});
