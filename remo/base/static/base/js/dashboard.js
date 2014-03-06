$(document).ready(function () {
    'use strict';

    // Continuouis reports containers
    var $cont_reports_mine_block = $('#dashboard-continuous-reports-mine-block');
    var $cont_reports_mentees_block = $('#dashboard-continuous-reports-mentees-block');
    var $cont_reports_all_block = $('#dashboard-continuous-reports-all-block');

    // Continuous reports buttons
    var $cont_reports_mine_button = $('#dashboard-continuous-reports-mine-button');
    var $cont_reports_mentees_button = $('#dashboard-continuous-reports-mentees-button');
    var $cont_reports_all_button = $('#dashboard-continuous-reports-all-button');

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

    $cont_reports_mine_button.on('click', function (e) {
        e.preventDefault();
        $cont_reports_mine_block.show('fast');
        $cont_reports_mentees_block.hide('fast');
        $cont_reports_all_block.hide('fast');

        $(this).parent().addClass('active');
        $cont_reports_mentees_button.parent().removeClass('active');
        $cont_reports_all_button.parent().removeClass('active');
    });

    $cont_reports_mentees_button.on('click', function (e) {
        e.preventDefault();
        $cont_reports_mentees_block.show('fast');
        $cont_reports_mine_block.hide('fast');
        $cont_reports_all_block.hide('fast');

        $(this).parent().addClass('active');
        $cont_reports_mine_button.parent().removeClass('active');
        $cont_reports_all_button.parent().removeClass('active');
    });

    $cont_reports_all_button.on('click', function (e) {
        e.preventDefault();
        $cont_reports_all_block.show('fast');
        $cont_reports_mentees_block.hide('fast');
        $cont_reports_mine_block.hide('fast');

        $(this).parent().addClass('active');
        $cont_reports_mine_button.parent().removeClass('active');
        $cont_reports_mentees_button.parent().removeClass('active');
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
