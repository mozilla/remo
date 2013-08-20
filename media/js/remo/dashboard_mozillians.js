$(document).ready(function () {
    $('.dashboard-mozillians-reps-grid-button').click(function () {
        $('.dashboard-mozillians-reps-grid-block').removeClass('hidden');
        $('.dashboard-mozillians-reps-reports-block').addClass('hidden');

        $('.dashboard-mozillians-reps-grid-button').parent().addClass('active');
        $('.dashboard-mozillians-reps-grid-button').parent().siblings().removeClass('active');
    });

    $('.dashboard-mozillians-reps-reports-button').click(function () {
        $('.dashboard-mozillians-reps-reports-block').removeClass('hidden');
        $('.dashboard-mozillians-reps-grid-block').addClass('hidden');

        $('.dashboard-mozillians-reps-reports-button').parent().addClass('active');
        $('.dashboard-mozillians-reps-reports-button').parent().siblings().removeClass('active');
    });

    $('.dashboard-events-future-button').click(function () {
        $('.dashboard-events-future-block').removeClass('hidden');
        $('.dashboard-events-past-block').addClass('hidden');

        $('.dashboard-events-future-button').parent().addClass('active');
        $('.dashboard-events-future-button').parent().siblings().removeClass('active');
    });

    $('.dashboard-events-past-button').click(function () {
        $('.dashboard-events-past-block').removeClass('hidden');
        $('.dashboard-events-future-block').addClass('hidden');

        $('.dashboard-events-past-button').parent().addClass('active');
        $('.dashboard-events-past-button').parent().siblings().removeClass('active');
    });

    $('table').each(function(index, item) { $(item).stupidtable(); });
    // Apply prettyDate on all elements with data-time attribute.
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC:true});

    $("a[data-reveal-id='mail-reps-modal']").click(function () {
        var area_id = $('#tracked-interests-tabs a.active').data('id');
        $('input[name=functional_area]').val(area_id);
    });
});
