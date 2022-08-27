/**
 * This file is part of MonitoraPA
 *
 * Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
 *
 * MonitoraPA is a hack. You can use it according to the terms and
 * conditions of the Hacking License (see LICENSE.txt)
 */
/* Detect Google Fonts collecting the fonts' urls
 * as an evidence of its presence
 */
 
debugger;

var fonts = []

// direct link to stylesheet
for(var sc of document.getElementsByTagName('link')){
    if(sc.rel != "preconnect" && sc.href.indexOf('//fonts.google') > -1) {
        console.log('MonitoraPA: found Google Fonts in ', sc);
        fonts.push(sc.href);
    }
}

// WebFont
if(fonts.length == 0){
    for(var sc of document.getElementsByTagName('script')){
        if(!sc.src){
            if(sc.text.indexOf('WebFont') > -1 && sc.text.indexOf('google') > -1){
                console.log('MonitoraPA: found Google Fonts in ', sc);
                fonts.push(sc.text.replaceAll(' ', '').replaceAll('\t', '').replaceAll('\n', ''));
            }
        }
    }
}

// CSS
if(fonts.length == 0){
    var regex = new RegExp('url\\\(.+?\\\)', 'ig');
    for(var sc of document.getElementsByTagName('style')){
        if(sc.type !== "text/css"){
            continue;
        }
        try{
            var cssText = sc.textContent;
            var urls = cssText.match(regex);
            if(!!urls && urls.length > 0){
                for(var i = 0; i<urls.length; ++i){
                    var candidate = urls[i];
                    if((candidate.indexOf('.woff') > -1 || candidate.indexOf('/css') > -1) 
                    && (candidate.indexOf('//fonts.google') > -1 || candidate.indexOf('//fonts.gstatic') > -1 || candidate.indexOf('//themes.googleusercontent') > -1) ) {
                        console.log('MonitoraPA: found Google Fonts in CSS: ', urls[i], sc);
                        fonts.push(candidate);
                    }
                }
            }
        } catch (e) {
            console.log('Monitora PA: exception while loading ', sc.href, e);
        }
    }
}

// CSS (external)
if(fonts.length == 0){
    var regex = new RegExp('url\\\(.+?\\\)', 'ig');
    for(var sc of document.getElementsByTagName('link')){
        if(sc.rel !== "stylesheet"){
            continue;
        }
        try{
            var cssText = monitoraPADownloadResource(sc.href);
            var urls = cssText.match(regex);
            if(!!urls && urls.length > 0){
                for(var i = 0; i<urls.length; ++i){
                    var candidate = urls[i];
                    if((candidate.indexOf('.woff') > -1 || candidate.indexOf('/css') > -1) 
                    && (candidate.indexOf('//fonts.google') > -1 || candidate.indexOf('//fonts.gstatic') > -1 || candidate.indexOf('//themes.googleusercontent') > -1) ) {
                        console.log('MonitoraPA: found Google Fonts in external CSS: ', urls[i], sc);
                        fonts.push(candidate);
                    }
                }
            }
        } catch (e) {
            console.log('Monitora PA: exception while loading ', sc.href, e);
        }
    }
}

if(fonts.length > 0){
    return JSON.stringify(fonts);
}
return "";
