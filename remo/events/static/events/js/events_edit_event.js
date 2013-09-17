$(document).ready(function() {
    // Move foundation elements to position.
    ['start', 'end'].forEach(function(obj) {
        ['0_month', '0_day', '0_year', '1_hour', '1_minute'].forEach(function(elem) {
            var destination = $('#' + obj + '-' + elem.substr(2));
            var form_elem = $('#id_' + obj + '_form_' + elem);
            var foundation_elem = form_elem.next().detach();

            form_elem.detach().appendTo(destination);
            foundation_elem.appendTo(destination);
        });
    });

    // Auto change end year, month, day when start changes.
    ['month', 'day', 'year'].forEach(function(when) {
        $('#id_start_form_0_' + when).change(function() {
            var obj = $('#id_end_form_0_' + when);
            obj.val($('#id_start_form_0_' + when).val());
            obj.trigger('change');
        });
    });

    // Dynamically add Metric forms
    $('form').on('click', '#events-add-metric-button', append_to_formset);
});
