/**
// @name        augement navigation button links
// @namespace   https://github.com/gqmaguirejr/E-learning
// @author      Gerald Q. Maguire Jr. <maguire@kth.se>
**/

(function() {
    'use strict';

    onPage(/\/courses\/\d+\/users/, function() {
	hasAnyRole('teacher', function(hasRole) {
	    if (hasRole) {
		// do something
		var link = document.getElementsByClassName('context_external_tool_2')[0]
		link.setAttribute('href',
				  link.getAttribute('href').concat('?url='+location.href))
		
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


