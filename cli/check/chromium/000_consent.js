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
    (new RegExp('^ok$', 'i')).compile(),
    (new RegExp('^accett[iao]', 'i')).compile(),
    (new RegExp('^acconsent', 'i')).compile(),
    (new RegExp('^approv[ao]', 'i')).compile(),
    (new RegExp('capito', 'i')).compile(),
    (new RegExp('^accept$', 'i')).compile(),
    (new RegExp('^accept all', 'i')).compile()
]

var findCookieBanner = function (){
    var elements = document.getElementsByTagName("div");
    var topZIndex = 0;
    var topElement = null;

    for (var i = 0; i < elements.length - 1; i++) {
        try{
            var zIndex = parseInt(window.getComputed(elements[i], null)['z-index']);
            
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
    for(var e = 0; e < elements.length; ++e){
        var element = elements[e];
        for(var i = 0; i < consentRegExps.length; ++i){
            var regexp = consentRegExps[i];
            if(regexp.test(e.innerText)){
                return element;
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
if(elementToClick){
    console.log("found consent button in ", elementToClick);
    window.monitoraPAUnloading = true;
    window.setTimeout(function(){
        elementToClick.click();
    }, 3000);
    return cookieBanner.innerText;
}

return "";
