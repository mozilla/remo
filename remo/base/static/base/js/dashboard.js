$(document).ready(function () {
    $('#dashboard-reports-all-button').click(function () {
        $('#dashboard-reports-all-block').show('fast');
        $('#dashboard-reports-my-block').hide('fast');
        $('#dashboard-reports-mentees-list-block').hide('fast');
        $('#dashboard-reports-mentees-grid-block').hide('fast');

        $(this).parent().addClass('active');
        $('#dashboard-reports-mine-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-grid-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-list-button').parent().removeClass('active');
    });

    $('#dashboard-reports-mine-button').click(function () {
        $('#dashboard-reports-my-block').show('fast');
        $('#dashboard-reports-all-block').hide('fast');
        $('#dashboard-reports-mentees-list-block').hide('fast');
        $('#dashboard-reports-mentees-grid-block').hide('fast');

        $(this).parent().addClass('active');
        $('#dashboard-reports-all-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-grid-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-list-button').parent().removeClass('active');
    });

    $('#dashboard-reports-mentees-list-button').click(function () {
        $('#dashboard-reports-mentees-list-block').show('fast');
        $('#dashboard-reports-my-block').hide('fast');
        $('#dashboard-reports-all-block').hide('fast');
        $('#dashboard-reports-mentees-grid-block').hide('fast');

        $(this).parent().addClass('active');
        $('#dashboard-reports-all-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-grid-button').parent().removeClass('active');
        $('#dashboard-reports-mine-button').parent().removeClass('active');
    });

    $('#dashboard-reports-mentees-grid-button').click(function () {
        $('#dashboard-reports-mentees-grid-block').show('fast');
        $('#dashboard-reports-mentees-list-block').hide('fast');
        $('#dashboard-reports-my-block').hide('fast');
        $('#dashboard-reports-all-block').hide('fast');

        $(this).parent().addClass('active');
        $('#dashboard-reports-all-button').parent().removeClass('active');
        $('#dashboard-reports-mentees-list-button').parent().removeClass('active');
        $('#dashboard-reports-mine-button').parent().removeClass('active');
    });

    $('#dashboard-br-all-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-br-my-block').hide('fast');
        $('#dashboard-br-mine-button').parent().removeClass('active');
        $('#dashboard-br-mentees-block').hide('fast');
        $('#dashboard-br-mentees-button').parent().removeClass('active');
        $('#dashboard-br-all-block').show('fast');
    });

    $('#dashboard-br-mine-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-br-my-block').show('fast');
        $('#dashboard-br-mentees-block').hide('fast');
        $('#dashboard-br-mentees-button').parent().removeClass('active');
        $('#dashboard-br-all-block').hide().parent().removeClass('active');
        $('#dashboard-br-all-button').parent().removeClass('active');
    });

    $('#dashboard-br-mentees-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-br-my-block').hide('fast');
        $('#dashboard-br-mine-button').parent().removeClass('active');
        $('#dashboard-br-mentees-block').show('fast');
        $('#dashboard-br-all-block').hide('fast');
        $('#dashboard-br-all-button').parent().removeClass('active');
    });

    $('#dashboard-sr-all-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-sr-my-block').hide('fast');
        $('#dashboard-sr-mine-button').parent().removeClass('active');
        $('#dashboard-sr-mentees-block').hide('fast');
        $('#dashboard-sr-mentees-button').parent().removeClass('active');
        $('#dashboard-sr-all-block').show('fast');
    });

    $('#dashboard-sr-mine-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-sr-my-block').show('fast');
        $('#dashboard-sr-mentees-block').hide('fast');
        $('#dashboard-sr-mentees-button').parent().removeClass('active');
        $('#dashboard-sr-all-block').hide().parent().removeClass('active');
        $('#dashboard-sr-all-button').parent().removeClass('active');
    });

    $('#dashboard-sr-mentees-button').click(function () {
        $(this).parent().addClass('active');
        $('#dashboard-sr-my-block').hide('fast');
        $('#dashboard-sr-mine-button').parent().removeClass('active');
        $('#dashboard-sr-mentees-block').show('fast');
        $('#dashboard-sr-all-block').hide('fast');
        $('#dashboard-sr-all-button').parent().removeClass('active');
    });

    $('table').each(function(index, item) { $(item).stupidtable(); });
    // Apply prettyDate on all elements with data-time attribute.
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC:true});
});
