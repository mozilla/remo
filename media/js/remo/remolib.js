function hash_set_value(key, value) {
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

    index_of_key = keys.indexOf(key);

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
}

function hash_get_value(key) {
    // Get value for key in hash
    var hash = $(location).attr('hash').substring(2).toLowerCase();
    var keys = hash.split('/').filter(function(element, index) { return (index % 2 === 0); });
    var values = hash.split('/').filter(function(element, index) { return (index % 2 === 1); });
    var index_of_key = keys.indexOf(key);
    if (index_of_key > -1) {
        return values[index_of_key].toLowerCase();
    }

    return;
}

function set_dropdown_value(elm, value) {
    elm.val(value);
    // We have to force trigger 'change' for foundation to update.
    elm.trigger('change');
}

function pad2(number) {
    // Pad numbers
    // snippet from
    // http://www.electrictoolbox.com/pad-number-two-digits-javascript/
    return (number < 10 ? '0' : '') + number;
}
