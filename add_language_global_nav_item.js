/**
// @name        augement navigation buttons
// @namespace   https://github.com/gqmaguirejr/E-learning
// @author      Gerald Q. Maguire Jr. <maguire@kth.se>
// @description Add a button labeled with the current language
**/

function toggleLanguage() {
    console.info("called  toggleLanguage")
//    '/api/v1/users/self?user[locale]=sv'
    var user=$.getJSON('/api/v1/users/self',
		       function (data){ var currentLocale=data['locale'];
					console.info("user's local is " + currentLocale + " type is" + typeof currentLocale);
					if (currentLocale == 'en') {
					    console.info("user's local  2 is ", currentLocale);
					    var newuser=$.post('/api/v1/users/self', {"_method": 'PUT',
										      "user[locale]": "sv"})
					    console.info("newuser is ", newuser)
					}
					else if (currentLocale == 'sv') {
					    console.info("user's local  2 is ", currentLocale);
					    var newuser=$.post('/api/v1/users/self', {"_method": 'PUT',
										      "user[locale]": "en"})
					    console.info("newuser is ", newuser)
					}

				      }

		      )
    //console.info("user is ", user)
    location.reload();
    return false;
}


// set the initial tab by adding a class "ui-tabs-active"
// <div class="enhanceable_content tabs">
// <ul>
// <li lang="en"><a href="#fragment-1">English</a></li>
// <li class="ui-tabs-active" lang="sv"><a href="#fragment-2">P&aring; svenska</a></li>
// </ul>

function modifyTabOrder() {
    console.info("called  swapTabOrder")
    if (ENV.LOCALE === 'en') {
	console.info("show English first");
	// $("div.enhanceable_content.tabs ul li[lang^='sv']").removeClass( "ui-tabs-active" )
	// $("div.enhanceable_content.tabs ul li[lang^='en']").addClass( "ui-tabs-active" );
	$("div.enhanceable_content.tabs ul li[lang^='en']").each(function() {
	    $(this).click();
	});
    }
    else if (ENV.LOCALE === 'sv') {
	console.info("show Swedish first");
	//  .ui-state-default .ui-corner-top
	//	$("div.enhanceable_content.tabs ul li[lang^='en']").removeClass( "ui-tabs-active" )
	//	$("div.enhanceable_content.tabs ul li[lang^='sv']").addClass( "ui-tabs-active" );
	$("div.enhanceable_content.tabs ul li[lang^='sv']").each(function() {
	    $(this).click();
	});
    }
}

(function(){
    'use strict';

    onPage(/\/courses/, function() {
	//	addMenuItem("http://www.kth.se", 'icon-settings-2')
	addMenuItem("#", 'icon-settings-2')
	setTimeout(modifyTabOrder, 1000);
	//modifyTabOrder();
    });





    function onPage(regex, fn) {
	if (location.pathname.match(regex)) fn();
    }

    function addMenuItem(linkhref, icon) {  
        var iconHtml = '',  
            itemHtml
        if (icon !== '') {  
            // If it is a Canvas icon  
           if (icon.indexOf('icon') === 0) {  
               iconHtml = '<div class="menu-item-icon-container" role="button" onclick="toggleLanguage();"><i class="' + icon + ' custom_menu_list_icon"></i></div>';  
               // for an svg or other image  
           } else if (icon !== '') {  
               iconHtml = '<div class="menu-item-icon-container" role="button" onclick="toggleLanguage();">' + icon + '</div>';  
  	   }
	}
	// Build item html  
	itemHtml = '<li class="ic-app-header__menu-list-item ">' +  
            '   <a id="global_nav_locale" href="' + linkhref + '" class="ic-app-header__menu-list-link">' + iconHtml +  
            '       <div class="menu-item__text custom-menu-item__text">' + ENV.LOCALE + '</div>' +  
            '   </a>' +  
            '</li>';  
	$('#menu').append(itemHtml);   
    }


})();
