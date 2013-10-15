$(document).ready(function(){
    // Load ReMo Planet.
    $('#planet').FeedEk({
        FeedUrl : 'http://planet.mozillareps.org/planet/posts/feeds/rss/',
        MaxCount : 3,
        ShowDesc : true,
        ShowPubDate:false
    });
});
