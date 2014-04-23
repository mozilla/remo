/* This script fix the progress bar for IE in case of overload */
$(document).ready(function() {
    $('.progressspan').each( function(i) {
        var $this = $(this);
        var percent = Math.min($this.data('percent'), 100);
        $this.css('width', percent + '%');
    });
});
