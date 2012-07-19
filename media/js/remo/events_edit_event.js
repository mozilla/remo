$(document).ready(function() {
    // Dynamically add Metric forms
    $('.metricblock').formset({
        formCssClass: 'dynamic-metric-form',
        prefix: 'eventmetric_set',
        addBtnObj: $('#events-add-metric-button'),
        addDeleteButton: null
    });
});
