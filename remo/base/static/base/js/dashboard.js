$(document).ready(function () {
    'use strict';

    // Reports containers
    var $reports_all_block = $('#dashboard-reports-all-block');
    var $reports_my_block = $('#dashboard-reports-my-block');
    var $mentees_list_block = $('#dashboard-reports-mentees-list-block');
    var $mentees_grid_block = $('#dashboard-reports-mentees-grid-block');

    // Reports buttons
    var $reports_mine_button = $('#dashboard-reports-mine-button');
    var $reports_mentees_grid_button = $('#dashboard-reports-mentees-grid-button');
    var $reports_mentees_list_button = $('#dashboard-reports-mentees-list-button');
    var $reports_all_button = $('#dashboard-reports-all-button');

    // Budget request buttons
    var $br_all_button = $('#dashboard-br-all-button');
    var $br_mine_button = $('#dashboard-br-mine-button');
    var $br_mentees_button = $('#dashboard-br-mentees-button');

    // Budget request containers
    var $br_my_block = $('#dashboard-br-my-block');
    var $br_mentees_block = $('#dashboard-br-mentees-block');
    var $br_all_block = $('#dashboard-br-all-block');

    // Swag request buttons
    var $sr_all_button = $('#dashboard-sr-all-button');
    var $sr_mine_button = $('#dashboard-sr-mine-button');
    var $sr_mentees_button = $('#dashboard-sr-mentees-button');

    // Swag request containers
    var $sr_mentees_block = $('#dashboard-sr-mentees-block');
    var $sr_all_block = $('#dashboard-sr-all-block');
    var $sr_my_block = $('#dashboard-sr-my-block');

    $reports_all_button.on('click', function (e) {
        e.preventDefault();
        $reports_all_block.show('fast');
        $reports_my_block.hide('fast');
        $mentees_list_block.hide('fast');
        $mentees_grid_block.hide('fast');

        $(this).parent().addClass('active');
        $reports_mine_button.parent().removeClass('active');
        $reports_mentees_grid_button.parent().removeClass('active');
        $reports_mentees_list_button.parent().removeClass('active');
    });

    $reports_mine_button.on('click', function (e) {
        e.preventDefault();
        $reports_my_block.show('fast');
        $reports_all_block.hide('fast');
        $mentees_list_block.hide('fast');
        $mentees_grid_block.hide('fast');

        $(this).parent().addClass('active');
        $reports_all_button.parent().removeClass('active');
        $reports_mentees_grid_button.parent().removeClass('active');
        $reports_mentees_list_button.parent().removeClass('active');
    });

    $reports_mentees_list_button.on('click', function (e) {
        e.preventDefault();
        $mentees_list_block.show('fast');
        $reports_my_block.hide('fast');
        $reports_all_block.hide('fast');
        $mentees_grid_block.hide('fast');

        $(this).parent().addClass('active');
        $reports_all_button.parent().removeClass('active');
        $reports_mentees_grid_button.parent().removeClass('active');
        $reports_mine_button.parent().removeClass('active');
    });

    $reports_mentees_grid_button.on('click', function (e) {
        e.preventDefault();
        $mentees_grid_block.show('fast');
        $mentees_list_block.hide('fast');
        $reports_my_block.hide('fast');
        $reports_all_block.hide('fast');

        $(this).parent().addClass('active');
        $reports_all_button.parent().removeClass('active');
        $reports_mentees_list_button.parent().removeClass('active');
        $reports_mine_button.parent().removeClass('active');
    });

    $br_all_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $br_my_block.hide('fast');
        $br_mine_button.parent().removeClass('active');
        $br_mentees_block.hide('fast');
        $br_mentees_button.parent().removeClass('active');
        $br_all_block.show('fast');
    });

    $br_mine_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $br_my_block.show('fast');
        $br_mentees_block.hide('fast');
        $br_mentees_button.parent().removeClass('active');
        $br_all_block.hide().parent().removeClass('active');
        $br_all_button.parent().removeClass('active');
    });

    $br_mentees_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $br_my_block.hide('fast');
        $br_mine_button.parent().removeClass('active');
        $br_mentees_block.show('fast');
        $br_all_block.hide('fast');
        $br_all_button.parent().removeClass('active');
    });

    $sr_all_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $sr_my_block.hide('fast');
        $sr_mine_button.parent().removeClass('active');
        $sr_mentees_block.hide('fast');
        $sr_mentees_button.parent().removeClass('active');
        $sr_all_block.show('fast');
    });

    $sr_mine_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $sr_my_block.show('fast');
        $sr_mentees_block.hide('fast');
        $sr_mentees_button.parent().removeClass('active');
        $sr_all_block.hide().parent().removeClass('active');
        $sr_all_button.parent().removeClass('active');
    });

    $sr_mentees_button.on('click', function (e) {
        e.preventDefault();
        $(this).parent().addClass('active');
        $sr_my_block.hide('fast');
        $sr_mine_button.parent().removeClass('active');
        $sr_mentees_block.show('fast');
        $sr_all_block.hide('fast');
        $sr_all_button.parent().removeClass('active');
    });

    $('table').each(function(index, item) {
        $(item).stupidtable();
    });

    // Apply prettyDate on all elements with data-time attribute.
    prettyDate();
});
