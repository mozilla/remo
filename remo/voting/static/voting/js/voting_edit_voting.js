$(document).ready(function() {
    // Move foundation elements to position.
    ['start', 'end'].forEach(function(obj) {
        ['0_month', '0_day', '0_year', '1_hour', '1_minute'].forEach(function(elem) {
            var destination = $('#' + obj + '-' + elem.substr(2));
            var form_elem = $('#id_' + obj + '_form_' + elem);

            form_elem.detach().appendTo(destination);
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

    // adds a poll copyblock to the form using JS template
    function add_poll_to_form($tpl, target, block) {
        var $formset_obj = $(target).closest('.formset');
        var prefix = $formset_obj.data('prefix');
        var $total_fields = $('#id_' + prefix + '-TOTAL_FORMS');
        var $last_obj = $formset_obj.find(block).last();
        var number_of_fields = parseInt($total_fields.val(), 10);

        // form data to pass to the template
        var data = {
            prefix: prefix,
            count: number_of_fields
        };
        //Compile the template
        var source = $tpl.html();
        var template = Handlebars.compile(source);
        // insert the new given poll as last object in the formset
        $(template(data)).insertAfter($last_obj);

        // update the total number of given fields
        $total_fields.val(number_of_fields + 1);
    }

    // add choice to radio poll from template
    function add_radio_choice_to_poll(e) {
        e.preventDefault();
        add_poll_to_form($('#radio-choice-tmpl'), e.currentTarget, '.radio-choice');
    }

    // add nominee to range poll from template
    function add_nominee_to_poll(e) {
        e.preventDefault();
        add_poll_to_form($('#nominee-tmpl'), e.currentTarget, '.nominee');
    }

    // creates a new radio poll from template
    function add_radio_poll(e) {
        e.preventDefault();
        add_poll_to_form($('#radio-poll-tmpl'), e.currentTarget, '.voting-poll');
    }

    // creates a new range poll from template
    function add_range_poll(e) {
        e.preventDefault();
        add_poll_to_form($('#range-poll-tmpl'), e.currentTarget, '.voting-poll');
    }

    // bind events
    $('#radio-poll-voting').on('click', '.voting-add-answer-button', add_radio_choice_to_poll);
    $('#range-poll-voting').on('click', '.voting-add-nominee-button', add_nominee_to_poll);
    $('.voting-add-rangepoll-button').on('click', add_range_poll);
    $('.voting-add-radiopoll-button').on('click', add_radio_poll);
});
