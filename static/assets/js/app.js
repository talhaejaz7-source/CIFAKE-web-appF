$(document).ready(function () {
	backgroundImage();
	$(document).on("scroll", onScroll);

	$(window).bind('scroll', function () {
		if ($(window).scrollTop() > 5) {
			$('.sticky-wrapper').addClass('is-sticky');
		} else {
			$('.sticky-wrapper').removeClass('is-sticky');
		}
	});

	$('a.nav-link[href^="#"]').on('click', function(event) {

		var target = $(this.getAttribute('href'));

		if( target.length ) {
			event.preventDefault();
			$('html,body').stop().animate({
				scrollTop: target.offset().top
			}, 1300);
		}

	});

	$('.navbar-header .navbar-nav .nav-item a[href^="#"]').on('click', function() {
		$('a').each(function () {
			$(this).parent().removeClass('active');
		})
		$(this).parent().addClass('active');
	})
});

function onScroll(event){
	var scrollPos = $(document).scrollTop();
	$('.navbar-header .navbar-nav .nav-item a[href^="#"]').each(function () {
		var parentLink = $(this).parent();
		var refElement = $($(this).attr("href"));
		if (refElement.position().top <= scrollPos && refElement.position().top + refElement.height() > scrollPos) {
			$(this).parent().removeClass("active");
			parentLink.addClass("active");
		}
		else{
			parentLink.removeClass("active");
		}
	});
}

function backgroundImage() {
	$('[data-image]').each(function() {
		$(this).css('background-image', 'url("' + $(this).attr('data-image') + '")');
	})
}