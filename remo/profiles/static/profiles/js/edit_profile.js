(function($) {
    'use strict';

    $('input:checkbox[id*="-bit"]').on('click', function() {
        if ($(this).attr('id') === 'alumni-bit') {
            if ($(this).is(':checked')){
                $('ul.edit-profile-item li input:checkbox[id*="-bit"]').not($(this)).prop('checked', false);
            }
        }
        else {
            $('input:checkbox[id="alumni-bit"]').prop('checked', false);
        }
    });

})(jQuery);
