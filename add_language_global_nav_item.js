/**
// @name        augement navigation buttons
// @namespace   https://github.com/gqmaguirejr/E-learning
// @author      Gerald Q. Maguire Jr. <maguire@kth.se>
// @description Add a button labeled with the current language
**/

(function() {
    'use strict';

    onPage(/\/courses/, function() {
	addMenuItem("http://www.kth.se", 'icon-settings-2')

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
               iconHtml = '<div class="menu-item-icon-container" role="presentation"><i class="' + icon + ' custom_menu_list_icon"></i></div>';  
               // for an svg or other image  
           } else if (icon !== '') {  
               iconHtml = '<div class="menu-item-icon-container" role="presentation">' + icon + '</div>';  
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


