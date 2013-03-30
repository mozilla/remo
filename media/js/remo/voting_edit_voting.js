$(document).ready(function() {
    //Code adapted from http://djangosnippets.org/snippets/1389/
    function updateElementIndex(el, prefix, ndx) {
        var id_regex = new RegExp('(' + prefix + '-\\d+-)');
        var replacement = prefix + '-' + ndx + '-';
        if ($(el).attr('for')) 
            $(el).attr('for', $(el).attr('for').replace(id_regex, replacement));
        if (el.id)
            el.id = el.id.replace(id_regex, replacement);
        if (el.name)
            el.name = el.name.replace(id_regex, replacement);

    }

    //Add formsets
    function addNestedForm(btn, classId, dataId) {
        var prefix = $('.' + classId).data(dataId);
        var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val(), 10);

        var row = $('.' + classId + ':first').clone(true).get(0);
        $('#id_' + prefix + '-TOTAL_FORMS', row).remove();
        $('#id_' + prefix + '-INITIAL_FORMS', row).remove();
        $('#id_' + prefix + '-MAX_NUM_FORMS', row).remove();
        // Insert it after the last form
        $(row).removeAttr('id').hide().insertAfter('.' + classId + ':last').slideDown(300);

        // Remove error messages
        $('.errorlist', row).remove();
        $(row).children().removeClass('error');

        $(row).children().each(function() {
            updateElementIndex(this, prefix, formCount);
            $(this).val('');
         });

        // Update total form count
        $('#id_' + prefix + '-TOTAL_FORMS').val(parseInt(formCount + 1, 10));

        return false;
    }

    function deleteNestedFormset(btn, classId, dataId) {
        var prefix = $('.' + classId).data(dataId);
        var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val(), 10);

        // We need at least one nested form
        if (formCount > 1) {
            $(btn).parents().parents().children('.' + classId + ':last').remove();
            var forms = $('.' + classId);

            $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
            var ctr = 0;
            for (formCount=forms.length; ctr < formCount; ctr++) {
                $(forms.get(ctr)).children().each(function() {
                    if ($(this).attr('type') == 'text')
                        updateElementIndex(this, prefix, ctr);
                });
            }
        }
        return false;
    }

    // Register click events
    $('#voting-add-poll-range-votes-button').click(function () {
        var classId = 'pollrangevotesblock';
        var dataId = 'nominee';
        return addNestedForm(this, classId, dataId);
    });

    $('#voting-add-poll-radio-choices-button').click(function () {
        var classId = 'pollradiochoicesblock';
        var dataId = 'choice';
        return addNestedForm(this, classId, dataId);
    });

    $('#voting-delete-poll-range-votes-button').click(function () {
        var classId = 'pollrangevotesblock';
        var dataId = 'nominee';
        return deleteNestedFormset(this, classId, dataId);
    });

    $('#voting-delete-poll-radio-choices-button').click(function () {
        var classId = 'pollradiochoicesblock';
        var dataId = 'choice';
       return deleteNestedFormset(this, classId, dataId);
    });

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
});
