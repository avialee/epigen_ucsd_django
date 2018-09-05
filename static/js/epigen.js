$.ajaxSetup({
    beforeSend: function(xhr, settings) {
	function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
		    var cookie = jQuery.trim(cookies[i]);
		    // Does this cookie string begin with the name we want?
		    if (cookie.substring(0, name.length + 1) == (name + '=')) {
			cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
			break;
		    }
		}
	    }
	    return cookieValue;
	}
	if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
	    // Only send the token to relative URLs i.e. locally.
	    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
	}
    }
});


$(document).ready( function () {
    $('.datatable').DataTable();

    $('.datatablesort5').DataTable({
    	"order": [[ 5, "desc" ]]
    });

    $('.datatablesort2').DataTable({
    	"order": [[ 2, "desc" ]]
    });
    
    $('.datatablesort1').DataTable({
		"order": [[ 1, "asc" ]]
    });

    $( "#id_date" ).datepicker();
    $( "#id_date_requested" ).datepicker();

    $('[data-toggle="tooltip"]').tooltip();

    $('.close').on('click',function() {
      $(this).closest('.row').fadeOut();
    });

    
    $('.formset_row').formset({
	addText: 'add another samples',
	deleteText: 'remove',
	prefix: 'librariesinrun_set'
    });

    $(".dmpajax").on("click",function(e){
	e.preventDefault();

	var runinfoid = this.id;
	var runinfoiddate = 'date-'+this.id
	var that = this;
	var url1=$(this).attr("data-href");
	var url2=url1.replace("demultiplexing","demultiplexing2")

	$.ajax({
	    url:url1,
	    cache:false,
	    dataType: 'json',
	    success:function (data){
		if (!data.is_direxists){
		    alert('Error: None of the folder name contains '+runinfoid)
		    return
		}
		if (data.mkdirerror){
		    alert(data.mkdirerror)
		    return
		}
		if (data.mkdirerror2){
		    
		    if (!confirm(data.mkdirerror2)){
			return 
		    }else{
			
			// nested ajex call DemultiplexingView2 to continue
			$.ajax({
			    type:"POST",
			    url:url2,
			    cache:false,
			    data: {somedata: 'somedata'}
			})
			$("#"+runinfoiddate).text(data.updatedate)
			$(that).replaceWith('<span class="badge badge-success badge-status-blue">JobSubmitted</span>')

			return
		    }

		}
		
		if (data.writesamplesheeterror){
		    alert(data.writesamplesheeterror)
		    return
		}
		if (data.writetosamplesheet){
		    $("#"+runinfoiddate).text(data.updatedate)
		    // $(that).removeClass('btn btn-danger btn-sm btn-status-orange dmpajax')
		    // $(that).addClass('btn btn-success btn-sm btn-status-green disabled');
		    $(that).replaceWith('<span class="badge badge-success badge-status-blue">JobSubmitted</span>')

		    return
		}

	    }

	});
    })

    var currenturl = window.location.pathname;
    if(currenturl.includes("update")){
    	
    	$("a.editable").addClass("active");

    }
    $("nav a").each(function(){
    	var href = $(this).attr("href");
    	if($(this).hasClass("dropdown-item")){
    		if(currenturl==href){
    			$(this).parent().prev("a").addClass("active");
    		}
    	}
    	else if(currenturl.split('/')[1]==$(this).attr("id")){
    		$(this).addClass("active")

    	}

    });
    $("#sidebar a").each(function(){
    	var href = $(this).attr("href");
    	if(currenturl==href){
    		if($(this).parent().hasClass("collapse")){
    			$(this).parent().prev("a").addClass("active");
    		}
    		else{
    			$(this).addClass("active")
    		}   		
    	}
    });

    $(".list-group.checkboxsidebar > .list-group-item").each(function(){
    	var checkitem = $(this);
    	var thisid = checkitem.attr("name")
    	checkitem.css('cursor','pointer');
    	checkbox = $('<input type="checkbox" style="display:none;" checked/>');
    	checkitem.prepend(checkbox);
    	var checkedicon = $('<i class="fas checkboxsidebar fa-check-square"></i>')
    	var uncheckedicon = $('<i class="far checkboxsidebar fa-square"></i>')
    	// checkitem.addClass("active");
    	checkitem.prepend(checkedicon)
    	var relatedsection = document.getElementById(thisid);
        checkbox.on('change',function(){
    		if(this.checked){
    			// checkitem.addClass("active");  
    			relatedsection.style.display = "block";
    			checkitem.find(".far").remove()
    			checkitem.prepend(checkedicon)

    		}
    		else{
    			// checkitem.removeClass("active");   			
    			relatedsection.style.display = "none";
    			checkitem.find(".fas").remove()
    			checkitem.prepend(uncheckedicon)

    		}
    	})

    })

} );
