$(document).ready(function () {
    $('.delete-object').click(function(e) {
        var form = $('#delete-modal > form');
        var target = $(this).attr('href');
        form.attr('action', target);
        $('#delete-activity').foundation('reveal', 'open');
    });
});
