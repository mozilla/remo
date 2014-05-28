(function($) {
    'use strict';

    /*
     * Toggles the replacement rep input field if a user selects to
     * be replaced by another Rep during the unavailability period.
     * Makes input a required field when it is visible,
     * removes input value when hidden.
     */
    function setReplacementRepPanel () {
        var choice = $('input[name="is_replaced"]:checked').val();
        var $panel = $('#replacement-rep-panel');
        var select = $panel.find('select');

        if (choice === 'True') {
            $panel.slideDown();
            select.attr('required', 'required');
        } else {
            $panel.slideUp();
            select.removeAttr('required');
            select.find('option:selected').prop('selected', false);
        }
    }


    // set date picker defaults
    initDatePicker(false);
    $('#replacement-rep-radio').on('change', setReplacementRepPanel);
    setReplacementRepPanel();

})(jQuery);
