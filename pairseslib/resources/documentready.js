	$(document).ready(function() {
		$(".fancybox").fancybox({
			arrows : false,
		    helpers : {
		        title: {
		            type: 'outside'
		        }
		    },
			loop: false,
			beforeShow : function() {
			   this.title = '#' + (this.index + 1) + (this.title ? ' ' + this.title : '');
			},
			afterShow : function() {	
				$('.fancybox-wrap').append($('<div style="clear:both;"></div>'));
				$('.fancybox-title').html($('.fancybox-title').text().replace(/__NEWLINE__/g,'<br>'));
				$('.fancybox-image').panzoom({
        			$zoomIn: $("#zoomin"),
        			$zoomOut: $("#zoomout")}
				);
				$("#zoomin").show();
				$("#zoomout").show();
			},
			afterClose : function() {
				$("#zoomin").hide();
				$("#zoomout").hide();
			}
		});
        

	});
