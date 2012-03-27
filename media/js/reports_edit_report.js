$(function() {
    $('.eventblock').formset({
        formCssClass: 'dynamic-event-form',
        prefix: 'reportevent_set',
        addBtnObj: $("#reports-add-event-button"),
        addDeleteButton: null
    });
    $('.linkblock').formset({
        formCssClass: 'dynamic-link-form',
        prefix: 'reportlink_set',
        addBtnObj: $("#reports-add-link-button"),
        addDeleteButton: null
    });

    $('#reports-submit-button').click(function(event) {
        event.preventDefault();
        past_items = $.trim($('#past_items').val());
        future_items = $.trim($('#future_items').val());

        if (past_items == '' && future_items == '') {
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

});
