$(document).ready(function() {
    $('.reports-submit-button').click(function(event) {
        event.preventDefault();
        past_items = $.trim($('#past_items').val());
        future_items = $.trim($('#future_items').val());

        if (past_items === '' && future_items === '') {
            $('#empty-report').reveal();
        }
        else {
            $('#reportform').submit();
        }
    });

    $('#reports-emptyreport-button').click(function(event) {
        event.preventDefault();
        $('#past_items').val('');
        $('#future_items').val('');
        $('#reportform').submit();
    });

    $('form.custom').on(
        'click', '#reports-add-link-button,#reports-add-event-button',
        append_to_formset);

});
