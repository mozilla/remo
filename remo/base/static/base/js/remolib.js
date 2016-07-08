function hash_set_value(key, value) {
    'use strict';
    // Set value for key in hash
    var hash = $(location).attr('hash').substring(2).toLowerCase().replace(/\/$/, '');
    var keys;
    var values;

    if (!value) {
        value = '';
    }

    if (hash.length > 0) {
        keys = hash.split('/').filter(function(element, index) { return (index % 2 === 0); });
        values = hash.split('/').filter(function(element, index) { return (index % 2 === 1); });
    }
    else {
        keys = [];
        values = [];
    }

    var index_of_key = keys.indexOf(key);

    if (index_of_key > -1) {
        values[index_of_key] = value;
    }
    else {
        keys.push(key);
        values.push(value);
    }

    hash = '/';
    for (var i=0; i < keys.length; i++) {
        if (values[i].length > 0 ) {
            hash += keys[i] + '/' + values[i] + '/';
        }
    }

    $(location).attr('hash', hash);

    (function() {
        var url = $("link[rel='shortcut icon']").remove().attr('href');
        var favicon = document.createElement('link');
        favicon.type = 'image/x-icon';
        favicon.rel = 'shortcut icon';
        favicon.href = url;
        $('head').append(favicon);
    }());

}

function hash_get_value(key) {
    'use strict';
    // Get value for key in hash
    var hash = $(location).attr('hash').substring(2).toLowerCase();
    var keys = hash.split('/').filter(function(element, index) { return (index % 2 === 0); });
    var values = hash.split('/').filter(function(element, index) { return (index % 2 === 1); });
    var index_of_key = keys.indexOf(key);
    if (index_of_key > -1) {
        return decodeURI(values[index_of_key].toLowerCase());
    }

    return;
}

function set_dropdown_value(elm, value) {
    'use strict';
    elm.val(value);
}

function pad2(number) {
    // Pad numbers
    // snippet from
    // http://www.electrictoolbox.com/pad-number-two-digits-javascript/
    'use strict';
    return (number < 10 ? '0' : '') + number;
}

function append_to_formset(event) {
    'use strict';
    event.preventDefault();
    var button_obj = $(event.currentTarget);
    var formset_obj = button_obj.closest('.formset');
    var block_obj = formset_obj.find('.copyblock').first();
    var new_block_obj = block_obj.clone();
    var prefix = formset_obj.data('prefix');
    var total_forms_obj = formset_obj.parent().children('#id_' + prefix + '-TOTAL_FORMS');
    var append_after_obj = block_obj;

    if (button_obj.hasClass('voting-add-rangepoll-button') ||
        button_obj.hasClass('voting-add-radiopoll-button')) {
        var input = new_block_obj.find('#inner-rangepoll-formset, #inner-radiopoll-formset');
        input.not(':first').remove();
    }

    if (block_obj.siblings('.copyblock').length > 0) {
        append_after_obj = block_obj.siblings('.copyblock').last();
    }

    function attr_update(selector, attr, prepend){
        new_block_obj.find(selector + prefix + "]").each(function (index, item) {
            var item_obj = $(item);
            var obj_length = total_forms_obj.val().length;
            var prologue_length = 2 + prepend.length + prefix.length + obj_length;
            var item_id = item_obj.attr(attr).substr(prologue_length - obj_length);
            var newid = prepend + prefix + '-' + total_forms_obj.val() + item_id;
            item_obj.attr(attr, newid);
        });
    }
    attr_update('[id*=id_', 'id', 'id_');
    attr_update('[name*=', 'name', '');
    attr_update('[data-prefix*=', 'data-prefix', '');
    attr_update('[for*=id_', 'for', 'id_');

    new_block_obj.insertAfter(append_after_obj);

    // Cleanup
    new_block_obj.find('input,select,textarea,label').each(function (index, item) {
        var item_obj = $(item);
        if (item_obj.is('input:hidden')) {
            return;
        }
        if (item_obj.is('input:checkbox') || item_obj.is('input:radio')) {
            item_obj.attr('checked', false);
        } else if (item_obj.is('select')) {
            item_obj.val($('options:first', item_obj).val());
            item_obj.trigger('change');
        } else {
            item_obj.val('');
        }
    });

    total_forms_obj.val(parseInt(total_forms_obj.val(), 10) + 1);
}

function format_hour(date_obj) {
    // Format date_obj to HH:MM.
    'use strict';
    return pad2(date_obj.getHours()) + ':' + pad2(date_obj.getMinutes());
}

function showMessage(options) {
    // Show a message the same way we use django messages
    'use strict';

    var defaults = {
        'id': '#client-message-container',
        'replace': false,
        'hide': false
    };

    options = $.extend(defaults, options);

    if (options.replace) {
        $('.message').remove();
    }

    var container = $(options.id).clone();
    container.removeAttr('id');
    container.addClass('message');
    container.insertAfter(options.id);

    var alertbox = container.children('.alert-box');
    alertbox.addClass(options.tag);
    alertbox.prepend(options.msg);

    container.show();

    if (options.hide) {
        setTimeout(function() {container.hide();}, 5000);
    }

}

function prettyDate() {
    'use strict';
    $('*').find('*[data-time]').prettyDate({attribute:'data-time', interval: 60000, isUTC:true});
}

function paginatorSelector(selector) {
    'use strict';
    selector = typeof selector !== 'undefined' ? selector : '#page-select';
    $(selector).on('change', function() {
        window.location = $(this).val();
    });
}

function addAttributionOSM(map) {
    var attribution = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors';
    map.attributionControl.addAttribution(attribution);
}

/*
 * Initialize date picker widget and set ISO date format
 * If the field is empty, pre-populate with current date
 * unless is explicity defined not to
 */
function initDatePicker (prepopulate_date) {
    var prepopulate_flag = (prepopulate_date === undefined) ? true : false;
    var $input = $('input.datepicker');
    $input.datepicker({
        autoSize: true,
        dateFormat: 'dd MM yy'
    });

    if ($input.val() === '' && prepopulate_flag) {
        var now = new Date();
        var today = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
        $input.datepicker('setDate', today);
    }
    else {
        var savedDate = new Date($input.val());
        $input.datepicker('setDate', savedDate);
    }
}
