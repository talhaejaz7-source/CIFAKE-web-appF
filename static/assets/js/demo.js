$(document).ready(function($){

	var openCustom = false;
	$styleCustom = $('#style-custom');

	$('#style-custom .open').click(function(){
		if (openCustom) {
			$styleCustom.css('right', '-190px');
			openCustom = false;
		} else {
			$styleCustom.css('right', '0px');
			openCustom = true;
		}
	});

	$("ul.pattern .color1" ).click(function(){
		$("#color-opt").attr("href", "assets/css/default.min.css" );
		return false;
	});
	$("ul.pattern .color2" ).click(function(){
		$("#color-opt").attr("href", "assets/css/cyan.min.css" );
		return false;
	});
	$("ul.pattern .color3" ).click(function(){
		$("#color-opt").attr("href", "assets/css/blue.min.css" );
		return false;
	});
	$("ul.pattern .color4" ).click(function(){
		$("#color-opt").attr("href", "assets/css/purple.min.css" );
		return false;
	});
	$("ul.pattern .color5" ).click(function(){
		$("#color-opt").attr("href", "assets/css/pink.min.css" );
		return false;
	});
	$("ul.pattern .color6" ).click(function(){
		$("#color-opt").attr("href", "assets/css/red.min.css" );
		return false;
	});
	$("ul.pattern .color7" ).click(function(){
		$("#color-opt").attr("href", "assets/css/yellow.min.css" );
		return false;
	});
	$("ul.pattern .color8" ).click(function(){
		$("#color-opt").attr("href", "assets/css/orange.min.css" );
		return false;
	});
	$("ul.pattern .color9" ).click(function(){
		$("#color-opt").attr("href", "assets/css/coffee.min.css" );
		return false;
	});
})