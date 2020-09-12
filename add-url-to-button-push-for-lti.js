/**
// @name        augement navigation button links
// @namespace   https://github.com/gqmaguirejr/E-learning
// @author      Gerald Q. Maguire Jr. <maguire@kth.se>
// @description Extend the URL of buttons for external tools with URL of the page we are on.
**/

(function() {
    'use strict';

    onPage(/\/courses\/\d+\/users/, function() {
	hasAnyRole('teacher', function(hasRole) {
	    if (hasRole) {
		// process all tools
		var links=document.querySelectorAll("[class^=context_external_tool_")
		var i;
		var link;
		for (i = 0; i < links.length; i++) {
		    link=links[i].getAttribute('href')
		    if (link.indexOf("?") == -1) {
			link=link.concat('?url='+location.href)
		    } else {
			// if there is already a question mark then there is a parameter
			link=link.concat('&url='+location.href)
		    }
		    links[i].setAttribute('href',link)
		}
	    } else {
		// do something else
	    }
	})});

    function onPage(regex, fn) {
	if (location.pathname.match(regex)) fn();
    }

    function hasAnyRole(/*roles, cb*/) {
	var roles = [].slice.call(arguments, 0);
	var cb = roles.pop();
	for (var i = 0; i < arguments.length; i++) {
	    if (ENV.current_user_roles.indexOf(arguments[i]) !== -1) {
		return cb(true);
	    }
	}
	return cb(false);
    }

})();


