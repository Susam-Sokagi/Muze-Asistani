$(document).ready(function () {
	$('#action_menu_btn').click(function () {
		$('.action_menu').toggle();
	});
});

$(document).ready(function () {
  $("#btnSubmit").click(function (event) {
    $.ajax({
      data: {
        message: $("textarea#message_text").val(),
      },
      type: "POST",
      url: "/",
    }).done(function (data) {
      $("#output").text(data.output).show();
    });
    event.preventDefault();
  });
});

$(document).ready(function (e) {
  $("#form").on("submit", function (e) {
	e.preventDefault();
    $.ajax({
      url: "http://api.qrserver.com/v1/read-qr-code/",
      type: "POST",
      data: new FormData(this),
      contentType: false,
      cache: false,
	  processData: false,
	  success:function(response){
		  if (response[0].symbol[0].error == null){
			  var data = response[0].symbol[0].data;
			  $("#preview").html(data).fadeIn();
			  $("#message-body").append(
		  '<div class="d-flex justify-content-start mb-4">' +
		  '<div class="img_cont_msg">' +
		  '<img src="https://d-tm.ppstatic.pl/kadry/1a/57/c1604c717078256513fdd67bd7de.1000.jpg" class="rounded-circle user_img_msg">' +
		  '</div><div class="msg_cotainer">' + data +
		  '<span class="msg_time">8:40, Bugün</span></div></div>'
        );
		  }
		  else{
			  console.log(response[0].symbol[0].error);
		  }
        },
      error: function (e) {
        $("#message_text").html(e).fadeIn();
      },
    });
  });
});
