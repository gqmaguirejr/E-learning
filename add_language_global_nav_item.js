/**
// @name        augement navigation buttons
// @namespace   https://github.com/gqmaguirejr/E-learning
// @author      Gerald Q. Maguire Jr. <maguire@kth.se>
// @description Add a button labeled with the current language
**/



function getUserLocale(data) {
    console.info("user's local is ", data['locale'])
}


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


(function() {
    'use strict';

    onPage(/\/courses/, function() {
	//	addMenuItem("http://www.kth.se", 'icon-settings-2')
	addMenuItem("#", 'icon-settings-2')

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
