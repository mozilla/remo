$(document).ready(function() {
    // Dynamically add Metric forms
    $('.metricblock').formset({
        formCssClass: 'dynamic-metric-form',
        prefix: 'metrics',
        addBtnObj: $('#events-add-metric-button'),
        addDeleteButton: null
    });
});
