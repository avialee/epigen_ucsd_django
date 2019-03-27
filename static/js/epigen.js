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

    // datatable js related
    // https://stackoverflow.com/questions/10630853/change-values-of-select-box-of-show-10-entries-of-jquery-datatable
    $('.datatable').DataTable({
	"aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
	"iDisplayLength": 20
    });

    $('.datatablesort5').DataTable({
	"aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
	"iDisplayLength": 20,
    	"order": [[ 5, "desc" ]]
    });

    $('.datatablesort2').DataTable({
	"aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
	"iDisplayLength": 20,
    	"order": [[ 2, "desc" ]]
    });
    
    $('.datatablesort1').DataTable({
	"aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
	"iDisplayLength": 20,
	"order": [[ 1, "asc" ]]
    });


    $('#datatabledetailnotes').DataTable({
	"aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
	"iDisplayLength": 20,
    	"order": [[ 3, "desc" ],[ 1, "desc" ]],
    	"columnDefs": [ {
   	    "orderable":false,
   	    "targets": [0,-1,-2],            
        } ,
        // {
        // 	"className": 'details-control',
        // 	"targets": 0,
        // }

        ]

    });


    $('#datatabledetailnotes2').DataTable({
        "order": [[ 2, "desc" ]],
        "columnDefs": [ {
            "orderable":false,
            "targets": [0],            
        } ,

        ]

    });

    $('#datatabledetailnotes tbody').on('click', 'td.details-control', function () {
    	var thisurl=$(this).attr("data-href");
    	var tr = $(this).closest('tr');
    	if ($(this).hasClass("closing")){
    		$(this).removeClass("closing")
    		tr.next().closest(".detailnotes").remove()
    	}
    	else{
    		$(this).addClass("closing")

           	$.ajax({
           		url:thisurl,
           		cache:false,
           		dataType: 'json',
           		success:function (data){

           		if(data.notes){
           			tr.after('<tr class="detailnotes"><td class="detailnotes" colspan="8"><div class="detailnotes">Notes:'+data.notes+'</div></td></tr>')


           			}
           		}
           	})

    	}

    });


    $('#datatabledetailnotes2 tbody').on('click', 'td.details-control', function () {
        var thisurl=$(this).attr("data-href");
        var tr = $(this).closest('tr');
        if ($(this).hasClass("closing")){
            $(this).removeClass("closing")
            tr.next().closest(".detailnotes").remove()


        }
        else{
            $(this).addClass("closing")

            $.ajax({
                url:thisurl,
                cache:false,
                dataType: 'json',
                success:function (data){

                if(data.notes){
                    tr.after('<tr class="detailnotes"><td class="detailnotes" colspan="8"><div class="detailnotes">Notes:'+data.notes+'</div></td></tr>')


                    }
                }
            })

        }

    });

    $('select#nextseq_app_machine').on('change', function() {
        console.log(this.value);
        if (this.value.startsWith('IGM_')){
            console.log('ffffff');
            document.getElementById('id_Flowcell_ID').value = 'TBD_'+Math.floor(Math.random() * 1000);

        }
        else{
            document.getElementById('id_Flowcell_ID').value = '';
        }
    });



    var samplesurl=$('#collab_samples').attr("data-href");
    $('#collab_samples').DataTable({
    "iDisplayLength": 10,
    "processing": true,
    "ajax": {
         url: samplesurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "sample_id"},
            { "data": "date"},
            { "data": "sample_type"},
            { "data": "service_requested"},
            { "data": "status"},
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"]; 
            return '<a href="/epigen/samples/' + itemID + '">' + data + '</a>';
        }
    }], 
    });



    $('#collab_samples_com').DataTable({
        
    })


    var metasampsurl=$('#metadata_samples').attr("data-href");
    $('#metadata_samples').DataTable({
    dom: 'lBfrtip',
    buttons: [
        'excel',
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "order": [[ 2, "desc" ],[ 3, "desc" ]],
    "processing": true,
    "ajax": {
         url: metasampsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "sample_id"},
            { "data": "description"},
            { "data": "date"},
            { "data": "group__name"},
            { "data": "sample_type"},          
            { "data": "status"},
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    }], 
    });

    var metasampsurl=$('#metadata_samples_bio').attr("data-href");
    $('#metadata_samples_bio').DataTable({
    dom: 'lBfrtip',
    buttons: [
        'excel',
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "order": [[ 2, "desc" ],[ 3, "desc" ]],
    "processing": true,
    "ajax": {
         url: metasampsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "sample_id"},
            { "data": "description"},
            { "data": "date"},
            { "data": "group__name"},
            { "data": "sample_type"},            
            { "data": "status"},
            { "data": null, defaultContent: ""},
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 6,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a class="spacing" href="/metadata/sample/'+itemID+'/update/"><i class="fas fa-edit"></i></a><a onclick="return confirm(\'Are you sure you want to delete sample '+row["sample_id"]+'?\');" href="/metadata/sample/'+itemID+'/delete/"><i class="fas fa-trash-alt"></i></a>';
        }        

    }], 
    });

    var metalibsurl=$('#metadata_libs').attr("data-href");
    $('#metadata_libs').DataTable({
    dom: 'lBfrtip',
    buttons: [
        'excel',
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "processing": true,
    "order": [[ 4, "desc" ],[ 3, "desc" ]],
    "ajax": {
         url: metalibsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "library_id"},
            { "data": "sampleinfo__sample_id"},
            { "data": "sampleinfo__sample_type"},	
            { "data": "sampleinfo__description"},
            { "data": "sampleinfo__group__name"},
            { "data": "date_started"},
            { "data": "experiment_type"},
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/lib/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 1,
        "render": function ( data, type, row ) {
            var itemID = row["sampleinfo__id"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    },

    ], 
    });

    var metalibsurl=$('#metadata_libs_bio').attr("data-href");
    $('#metadata_libs_bio').DataTable({
    dom: 'lBfrtip',
    buttons: [
         'excel',
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "order": [[ 4, "desc" ],[ 3, "desc" ]],
    "processing": true,
    "ajax": {
         url: metalibsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "library_id"},
            { "data": "sampleinfo__sample_id"},
            { "data": "sampleinfo__sample_type"},		
            { "data": "sampleinfo__description"},
            { "data": "sampleinfo__group__name"},
            { "data": "date_started"},
            { "data": "experiment_type"},
            { "data": null, defaultContent: ""},
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/lib/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 1,
        "render": function ( data, type, row ) {
            var itemID = row["sampleinfo__id"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 7,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a class="spacing" href="/metadata/lib/'+itemID+'/update/"><i class="fas fa-edit"></i></a><a onclick="return confirm(\'Are you sure you want to delete library '+row["library_id"]+'?\');" href="/metadata/lib/'+itemID+'/delete/"><i class="fas fa-trash-alt"></i></a>';
        }        

    } 
    ], 
    });


    var metaseqsurl=$('#metadata_seqs').attr("data-href");
    $('#metadata_seqs').DataTable({
    dom: 'lBfrtip',
    buttons: [
        'excel', 
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "processing": true,
    "order": [[ 4, "desc" ],[ 3, "desc" ]],
    "ajax": {
         url: metaseqsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "seq_id"},
            { "data": "libraryinfo__sampleinfo__sample_id"},
            { "data": "libraryinfo__sampleinfo__description"},
            { "data": "libraryinfo__sampleinfo__group__name"},
            { "data": "date_submitted_for_sequencing"},
            { "data": "read_length"},
            { "data": "read_type"},
            
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/seq/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 1,
        "render": function ( data, type, row ) {
            var itemID = row["libraryinfo__sampleinfo__id"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    },

    ], 
    });


    var metaseqsurl=$('#metadata_seqs_bio').attr("data-href");
    $('#metadata_seqs_bio').DataTable({
    dom: 'lBfrtip',
    buttons: [
        'excel',
            {
                text: 'TSV',
                extend: 'csvHtml5',
                fieldSeparator: '\t',
                extension: '.tsv',
                fieldBoundary:''
            }
    ],
    "aLengthMenu": [[20, 50, 75, -1], [20, 50, 75, "All"]],
    "iDisplayLength": 20,
    "processing": true,
    "order": [[ 4, "desc" ],[ 3, "desc" ]],
    "ajax": {
         url: metaseqsurl,
         dataSrc: ''
        },
    "columns": [
            { "data": "seq_id"},
            { "data": "libraryinfo__sampleinfo__sample_id"},
            { "data": "libraryinfo__sampleinfo__description"},
            { "data": "libraryinfo__sampleinfo__group__name"},
            { "data": "date_submitted_for_sequencing"},
            { "data": "read_length"},
            { "data": "read_type"},
            { "data": null, defaultContent: ""},
            
        ],
    "deferRender": true,
    "select": true,

    "columnDefs": [{
        "targets": 0,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a href="/metadata/seq/' + itemID + '">' + data + '</a>';
        }
    },
    {
        "targets": 1,
        "render": function ( data, type, row ) {
            var itemID = row["libraryinfo__sampleinfo__id"];                   
            return '<a href="/metadata/sample/' + itemID + '">' + data + '</a>';
        }
    },

    {
        "targets": 7,
        "render": function ( data, type, row ) {
            var itemID = row["pk"];                   
            return '<a class="spacing" href="/metadata/seq/'+itemID+'/update/"><i class="fas fa-edit"></i></a><a onclick="return confirm(\'Are you sure you want to delete sequencing '+row["seq_id"]+'?\');" href="/metadata/seq/'+itemID+'/delete/"><i class="fas fa-trash-alt"></i></a>';
         }        

    } 
    ], 
    });
    
    $('.ajax_sampleinput_form').parent().addClass('ui-widget');
    $('.ajax_sampleinput_form').autocomplete({
        source: "/metadata/ajax/load-samples/",
        minLength:2,
    });

    $('.ajax_libinput_form').parent().addClass('ui-widget');
    $('.ajax_libinput_form').autocomplete({
        source: "/metadata/ajax/load-libs/",
        minLength:2,
    });

    $('.ajax_userinput_form').parent().addClass('ui-widget');
    $('.ajax_userinput_form').autocomplete({
        source: "/setqc/ajax/load-users/",
        minLength:2,
    });   


    $('#id_experiment_type').change(function (){
        var url = $("#librayspec").attr("data-protocal-url");
        var expId = $(this).val();
        $.ajax({
            url:url,
            data: {
                'exptype':expId
            },
            success:function (data){
                $("#id_protocalinfo").html(data);
            }
        })
    });

// $('[data-toggle="tabajax"]').click(function(e) {
//     var $this = $(this),
//         loadurl = $this.attr('href'),
//         targ = $this.attr('data-target');

//     $.get(loadurl, function(data) {
//         $(targ).html(data);
//     });

//     $this.tab('show');
//     return false;
// });

    $('#myModal').modal('show')
    $('#confirmtosave').on('click',function() {
      $( "#bindtomodalok" ).trigger( "click" );
    });   
    // $('#review-tab').on('click',function(e) {
    //   location.reload();
    //   $( "#previewsub" ).trigger( "click" );
      
    //   console.log(e)
    // });

    $( "#id_date" ).datepicker();
    $( "#id_date_requested" ).datepicker();
    $( "#id_date_started" ).datepicker();
    $( "#id_date_completed" ).datepicker();
    $( "#id_date_submitted_for_sequencing" ).datepicker();

    $('[data-toggle="tooltip"]').tooltip();

    $('.close').on('click',function() {
      $(this).closest('.row').fadeOut();
    });

    
    $('.formset_row').formset({
	addText: 'add another samples',
	deleteText: 'remove',
	prefix: 'librariesinrun_set'
    });

   $('.chipformset_row').formset({
    addText: 'add another group',
    deleteText: 'remove',
    prefix: 'form'
    });

    $('select#id_experiment_type').on('change', function() {
        if (this.value=="ChIP-seq" ){
            //document.getElementById('changeble_librariesform').innerHTML='{% include "setqc_app/libraiestoincludeformchip.html"%}'
            //location.reload();
            document.getElementById('regform').style.display = "none";
            document.getElementById('chipform').style.display = '';

        }
        else{
            document.getElementById('regform').style.display = '';
            document.getElementById('chipform').style.display = "none";
        }
    });
    //console.log(document.getElementById('changeble_librariesform'))
    var changeble_form = $('#changeble_librariesform').find("select#id_experiment_type option:selected").text()
    if (changeble_form=="ChIP-seq" ){
        $('#chipform').css('display','');
        $('#regform').css('display','none');
        

    }
    else{
        $('#regform').css('display','');
        $('#chipform').css('display','none');
    }

    
    $('form#chiponly').find("select#id_experiment_type option:not(:contains('ChIP-seq'))").attr('disabled','disabled')
    $('form#notchip').find("select#id_experiment_type option:contains('ChIP-seq')").attr('disabled','disabled')


    $("#id_samplesinfo").attr("wrap", "off");
    $("#id_libsinfo").attr("wrap", "off");
    $("#id_seqsinfo").attr("wrap", "off");
    $(".downloadajax").on("click",function(e){
        e.preventDefault();
        var runinfoid = this.id;
        
        var url1=$(this).attr("data-href");
        $( "#downloadingform").attr( "runid", runinfoid);
        $( "#downloadingform" ).attr( "data-href", url1);

    });
    $("#submitForm").on("click",function(e){
        $("#downloadingform").submit();


    });
     $("#downloadingform").on("submit",function(e){
        var runinfoid = $(this).attr("runid");
        var runinfoiddate = 'date-'+$(this).attr("runid")
        var runinfoidflow = 'flowcell-'+$(this).attr("runid")
        var postdata=$(this).serializeArray();
        var url1=$(this).attr("data-href");
        console.log(url1);
        $.ajax({
            url:url1,
            cache:false,
            type:"POST",
            data:postdata,
            success:function (data){
              if (data.parseerror){
                alert(data.parseerror)
                return
              }
              if (data.flowduperror){
                alert(data.flowduperror)
                return
              }
              $("#"+runinfoiddate).text(data.updatedate);
              $("#"+runinfoidflow).html(data.flowid);
              $("#downloadModal").modal("hide");
              $("#"+runinfoid).replaceWith('<span class="badge badge-success badge-status-blue">JobSubmitted</span>')

            }
        });
        e.preventDefault();

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

    $(".runsetqc").on("click",function(e){
        e.preventDefault();
        that = $(this)
        var url1=$(this).attr("data-href");
        var url2=url1.replace("runsetqc","runsetqc2")
        var errorname = ['notfinishederror','libdirnotexisterror','writeseterror','fastqerror']
        $.ajax({
        url:url1,
        cache:false,
        dataType: 'json',
        success:function (data){
            $.each(errorname, function( index, value ) {
                if (value in data){
                    alert(data[value])
                    return
                }
            });
            if (data.setidexisterror){
                
                if (!confirm(data.setidexisterror)){
                return 
                }else{
                
                $.ajax({
                  type:"POST",
                  url:url2,
                  cache:false,
                  data: {somedata: 'somedata'}
                  })
                $(that).replaceWith('<span class="badge badge-success badge-status-blue">JobSubmitted</span>')
                return
            }

        }
            if (data.writesetdone){
            $(that).replaceWith('<span class="badge badge-success badge-status-blue">JobSubmitted</span>')

            }


        }

        })
    })

} );
