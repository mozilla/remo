jQuery(document).ready(function ($) {
    /* Use this js doc for all application specific JS */
    /* TABS --------------------------------- */
    /* Remove if you don't need :) */

    function activateTab($tab) {
        var $activeTab = $tab.closest('dl').find('a.active'),
        contentLocation = $tab.attr("href") + 'Tab';

        // Strip off the current url that IE adds
        contentLocation = contentLocation.replace(/^.+#/, '#');

        //Make Tab Active
        $activeTab.removeClass('active');
        $tab.addClass('active');

        //Show Tab Content
        $(contentLocation).closest('.tabs-content').children('li').hide();
        $(contentLocation).css('display', 'block');
    }

    $('dl.tabs').each(function () {
        //Get all tabs
        var tabs = $(this).children('dd').children('a');
        tabs.click(function (e) {
            activateTab($(this));
        });
    });

    if (window.location.hash) {
        activateTab($('a[href="' + window.location.hash + '"]'));

        /* this is for legacy Foundation 2 TODO - remove after migration to 4 */
        if (typeof $.foundation !== 'undefined') {
            $.foundation.customForms.appendCustomMarkup();
        }

    }

    /* PLACEHOLDER FOR FORMS ------------- */
    /* Remove this and jquery.placeholder.min.js if you don't need :) */
    $('input, textarea').placeholder();


    /* DISABLED BUTTONS ------------- */
    /* Gives elements with a class of 'disabled' a return: false; */

    /* ALERT BOXES ------------ */
    var clearAlert = setTimeout(function(){
        $(".alert-box.success").fadeOut('slow');
    }, 5000);

    $(document).on("click", ".success a.close", function(event){
        clearTimeout(clearAlert);
    });

    $(document).on("click", ".alert-box a.close", function(event) {
        event.preventDefault();
        $(this).closest(".alert-box").fadeOut(function(event){
            $(this).remove();
        });
    });

});

if (typeof(L) != 'undefined') {
    L.Icon.Default.imagePath = '/static/base/js/images';
}
