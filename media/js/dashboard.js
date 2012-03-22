$(document).ready( function () {
    $("#dashboard-br-all-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-br-my-block").hide();
        $("#dashboard-br-mine-button").parent().removeClass("active");
        $("#dashboard-br-mentees-block").hide();
        $("#dashboard-br-mentees-button").parent().removeClass("active");
        $("#dashboard-br-all-block").show()
    });
    $("#dashboard-br-mine-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-br-my-block").show();
        $("#dashboard-br-mentees-block").hide();
        $("#dashboard-br-mentees-button").parent().removeClass("active");
        $("#dashboard-br-all-block").hide().parent().removeClass("active");
        $("#dashboard-br-all-button").parent().removeClass("active");
    });
    $("#dashboard-br-mentees-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-br-my-block").hide();
        $("#dashboard-br-mine-button").parent().removeClass("active");
        $("#dashboard-br-mentees-block").show();
        $("#dashboard-br-all-block").hide()
        $("#dashboard-br-all-button").parent().removeClass("active");
    });

    $("#dashboard-sr-all-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-sr-my-block").hide();
        $("#dashboard-sr-mine-button").parent().removeClass("active");
        $("#dashboard-sr-mentees-block").hide();
        $("#dashboard-sr-mentees-button").parent().removeClass("active");
        $("#dashboard-sr-all-block").show()
    });
    $("#dashboard-sr-mine-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-sr-my-block").show();
        $("#dashboard-sr-mentees-block").hide();
        $("#dashboard-sr-mentees-button").parent().removeClass("active");
        $("#dashboard-sr-all-block").hide().parent().removeClass("active");
        $("#dashboard-sr-all-button").parent().removeClass("active");
    });
    $("#dashboard-sr-mentees-button").click(function() {
        $(this).parent().addClass("active")
        $("#dashboard-sr-my-block").hide();
        $("#dashboard-sr-mine-button").parent().removeClass("active");
        $("#dashboard-sr-mentees-block").show();
        $("#dashboard-sr-all-block").hide()
        $("#dashboard-sr-all-button").parent().removeClass("active");
    });

})
