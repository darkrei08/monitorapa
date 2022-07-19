/**
 * This file is part of MonitoraPA
 *
 * Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
 *
 * MonitoraPA is a hack. You can use it according to the terms and
 * conditions of the Hacking License (see LICENSE.txt)
 */
/* Detect (and click) Cookie Consent Button and collect its innerText.
 *
 * This check apply some heuristics to identify the consent button.
 */

var consentRegExps = [
    (new RegExp('^ok$', 'i')),
    (new RegExp('accett[iao] tutti', 'i')),
    (new RegExp('accett[iao]', 'i')),
    (new RegExp('^acconsent', 'i')),
    (new RegExp('^approv[ao]', 'i')),
    (new RegExp('capito', 'i')),
    (new RegExp('^accept$', 'i')),
    (new RegExp('^accept all', 'i')),
    (new RegExp('allow', 'i'))
]

var findCookieBanner = function (){
    var elements = document.getElementsByTagName("div");
    var topZIndex = 0;
    var topElement = null;

    for (var i = 0; i < elements.length; i++) {
        try{
            var zIndex = parseInt(window.getComputedStyle(elements[i], null)['z-index']);
            if (zIndex > topZIndex && elements[i].innerText.toLowerCase().indexOf('cookie') > -1) {
                topElement = elements[i];
                topZIndex = zIndex;
            }
        } catch {
        }
    }
    
    return topElement;
}
var findElementToClick = function(elements){
    for(var e = elements.length; e > 0 ; --e){
        var element = elements[e-1];
        var elementStyles = window.getComputedStyle(element, null);
        if(elementStyles['visibility'] == 'visible' && element.getClientRects().length > 0){        
            for(var i = 0; i < consentRegExps.length; ++i){
                var regexp = consentRegExps[i];
                if(regexp.test(element.innerText)){
                    return element;
                }
            }
        }
    }
    return null;
}

var cookieBanner = findCookieBanner();

if (!cookieBanner){
    return "";
}

var buttons = cookieBanner.querySelectorAll("button");
var elementToClick = findElementToClick(buttons);
if(!elementToClick){
    var links = cookieBanner.querySelectorAll("a");
    elementToClick = findElementToClick(links);
}
if(!elementToClick){
    var spans = cookieBanner.querySelectorAll("span");
    elementToClick = findElementToClick(spans);
}
if(!elementToClick){
    var divs = cookieBanner.querySelectorAll("divs");
    elementToClick = findElementToClick(spans);
}
if(elementToClick){
    console.log("found consent button in ", elementToClick);
    monitoraPAClick(elementToClick);
    return "<" + elementToClick.innerText + "> " + cookieBanner.innerText;
}

return "";
