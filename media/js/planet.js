$(document).ready(function(){
        $('#planet').FeedEk({
                FeedUrl : 'http://planet.mozillareps.org/planet/posts/feeds/rss/',
                MaxCount : 3,
                ShowDesc : true,
                ShowPubDate:false
        });
});
