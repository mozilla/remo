// WebTrends SmartSource Data Collector Tag v10.2.10
// Copyright (c) 2012 Webtrends Inc.  All rights reserved.
// Tag Builder Version: 4.1.0.10
// Created: 2012.05.15
//
// Modified to support DNT

(function(){
    var dnt = navigator.doNotTrack || navigator.msDoNotTrack;
    if (!dnt || (dnt && (dnt != 'yes' && dnt != '1'))) {
        window.webtrendsAsyncInit=function(){
            var dcs=new Webtrends.dcs().init({
                dcsid:"dcsn9zlfduz5bdwdlv6uznm5h_6i3i",
                domain:"statse.webtrendslive.com",
                timezone:0,
                fpcdom:".reps.mozilla.org",
                plugins:{
                    //hm:{src:"//s.webtrends.com/js/webtrends.hm.js"}
                }
            }).track();
        };

        var s=document.createElement("script");
        s.async=true;
        var surl =$("#webtrends-url").data('url');
        s.src = surl.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#34;/g, '"').split('"')[1];
        var s2=document.getElementsByTagName("script")[0];
        s2.parentNode.insertBefore(s,s2);
    }
}());
