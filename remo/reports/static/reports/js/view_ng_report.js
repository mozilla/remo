(function($) {
    'use strict';

    /*
     * Makes the checkbox input field visible, if the activity
     * of the report is "Recruited a Mozillian".
     */

    function showVerificationBox () {
        var $checkbox = $('#verification-checkbox');
        var triggerInput = $('#view-ngreport-form').data('verification-trigger');

        if (triggerInput === 'Recruited a Mozillian') {
            $checkbox.slideDown();
        }
    }

    showVerificationBox();
})(jQuery);
