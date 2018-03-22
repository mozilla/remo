function set_time_tooltip() {
    'use strict';
    // Set time tooltip to display the time to your browser's timezone.
    var title = '';
    var item = $('.datetime-tip');

    var start_date = new Date(item.data('date-start'));
    var user_start_date = new Date(item.data('date-start'));
    user_start_date.setHours(start_date.getHours(),
                             start_date.getMinutes() - start_date.getTimezoneOffset());
    var end_date = new Date(item.data('date-end'));
    var user_end_date = new Date(item.data('date-end'));
    user_end_date.setHours(end_date.getHours(),
                           end_date.getMinutes() - end_date.getTimezoneOffset());

    title = ('Voting starts from ' +
             format_hour(start_date) +
             ' to ' +
             format_hour(end_date) +
             ' (UTC) or ' +
             'from ' + format_hour(user_start_date) + ' to ' +
             format_hour(user_end_date) + ' local time.');

    // We need to add title, add class and call tooltips() after we
    // have initialized the tooltip.
    item.attr('title', title);
    item.addClass('has-tip');
}

$(document).ready(function() {
    'use strict';
    set_time_tooltip();
    prettyDate();
});
