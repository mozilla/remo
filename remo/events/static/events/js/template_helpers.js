function eventDate() {
    var s = new Date(this.local_start);

    if (this.multiday) {
        var e = new Date(this.local_end);
        return s.getDate() + '-' + e.getDate();
    }
    return s.getDate();
}


function isMultiMonth(event) {
    event = typeof event !== 'undefined' ? event: this;
    var s = new Date(event.local_start);
    var e = new Date(event.local_end);
    return s.getMonth() != e.getMonth();
}


function eventMonth() {
    var monthNames = [ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ];

        if (this.multiday) {
            var s = new Date(this.local_start);
            var e = new Date(this.local_end);

            // Also check if multimonth
            if (isMultiMonth(this)) {
                return monthNames[s.getMonth()] + '-' + monthNames[e.getMonth()];
            }
        }
        d = new Date(this.local_start);
        return monthNames[d.getMonth()];
}


function eventYear() {
    var s = new Date(this.local_start);
    return s.getFullYear();
}


Handlebars.registerHelper('getEventDate', eventDate);
Handlebars.registerHelper('getEventMonth', eventMonth);
Handlebars.registerHelper('isEventMultiMonth', isMultiMonth);
Handlebars.registerHelper('getEventYear', eventYear);
