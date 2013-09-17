$(document).ready(function () {
    $('a.featured-delete').click(function (e) {
        e.preventDefault();
        $(this).closest('form').submit();
    });
});

