$(document).ready(function () {
    $("#dashboard-br-all-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-br-my-block").hide('fast');
        $("#dashboard-br-mine-button").parent().removeClass("active");
        $("#dashboard-br-mentees-block").hide('fast');
        $("#dashboard-br-mentees-button").parent().removeClass("active");
        $("#dashboard-br-all-block").show('fast');
    });
    $("#dashboard-br-mine-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-br-my-block").show('fast');
        $("#dashboard-br-mentees-block").hide('fast');
        $("#dashboard-br-mentees-button").parent().removeClass("active");
        $("#dashboard-br-all-block").hide().parent().removeClass("active");
        $("#dashboard-br-all-button").parent().removeClass("active");
    });
    $("#dashboard-br-mentees-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-br-my-block").hide('fast');
        $("#dashboard-br-mine-button").parent().removeClass("active");
        $("#dashboard-br-mentees-block").show('fast');
        $("#dashboard-br-all-block").hide('fast');
        $("#dashboard-br-all-button").parent().removeClass("active");
    });

    $("#dashboard-sr-all-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-sr-my-block").hide('fast');
        $("#dashboard-sr-mine-button").parent().removeClass("active");
        $("#dashboard-sr-mentees-block").hide('fast');
        $("#dashboard-sr-mentees-button").parent().removeClass("active");
        $("#dashboard-sr-all-block").show('fast');
    });
    $("#dashboard-sr-mine-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-sr-my-block").show('fast');
        $("#dashboard-sr-mentees-block").hide('fast');
        $("#dashboard-sr-mentees-button").parent().removeClass("active");
        $("#dashboard-sr-all-block").hide().parent().removeClass("active");
        $("#dashboard-sr-all-button").parent().removeClass("active");
    });
    $("#dashboard-sr-mentees-button").click(function () {
        $(this).parent().addClass("active");
        $("#dashboard-sr-my-block").hide('fast');
        $("#dashboard-sr-mine-button").parent().removeClass("active");
        $("#dashboard-sr-mentees-block").show('fast');
        $("#dashboard-sr-all-block").hide('fast');
        $("#dashboard-sr-all-button").parent().removeClass("active");
    });

});
