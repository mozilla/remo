(function($) {
    'use strict';

    function disableRotmSubmitButton () {
        var button = $('#submit-rotm-form');
        var isNominated = (button.data('user-nominated')) === 'True' ? true : false;

        if (isNominated) {
            button.attr('disabled', 'disabled');
        } else {
            button.removeAttr('disabled');
        }

    }

    // Enable/Disable submit button on page load
    disableRotmSubmitButton();

})(jQuery);

