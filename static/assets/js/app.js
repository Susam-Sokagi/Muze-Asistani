// Chat Ayarları Menüsü Display Özelliği
$(document).ready(function () {
  $("#action_menu_btn").click(function () {
    $(".action_menu").toggle();
  });
});

// Upload Butonu Display Özelliği
$(document).ready(function () {
  $("#attach").click(function () {
    $("#upload-button").css("display", "inherit");
  });
});

// Backend ile mesajlaşma fonksiyonu
$(document).ready(function () {
  $("#btnSubmit").click(function (event) {
    message = $("textarea#message_text").val();
    // Boş mesaj içeriği kontrolü ve uyarısı.
    if (message === "") {
      alert("Lütfen boş metin içeren bir mesaj göndermeye çalışmayınız !");
    } else {
      var today = new Date();
      //var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
      var time = today.getHours() + ":" + today.getMinutes();
      //var dateTime = date+' | '+time;
      // Kullanıcının yazdığı mesajın ekrana basılması.
      $("#message-body").append(
        '<div class="d-flex justify-content-end mb-4">' +
        '<div class="msg_cotainer_send">' +
        message +
        '<span class="msg_time_send"> '+ time +' </span></div>' +
        '<div class="img_cont_msg">' +
        '<img src="https://i.hizliresim.com/lI85WY.png" class="rounded-circle user_img_msg">' +
        "</div></div>"
      );
      $("#message-body").animate(
        { scrollTop: $("#message-body")[0].scrollHeight },
        1000
      );
      $("#message_text").val("");
      // Kullanıcının yazdığı mesajın AJAX ile backend uygulamasına POST atılması.
      $.ajax({
        data: {
          message: message,
        },
        type: "POST",
        url: "/answer",
        // Başarılı sonuçlanan AJAX fonksiyonu eylemi
        success: function (response) {
          if (response != null) {
            var today = new Date();
            //var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            var time = today.getHours() + ":" + today.getMinutes();
            //var dateTime = date+' | '+time;
            var data = response;
            // Backend'den gelen cevabın ekrana bot tarafından yazılıyor gibi basılması.
            $("#message-body").append(
              '<div class="d-flex justify-content-start mb-4">' +
              '<div class="img_cont_msg">' +
              '<img src="https://avatars3.githubusercontent.com/u/68184733?s=200&v=4" class="rounded-circle user_img_msg">' +
              '</div><div class="msg_cotainer">' +
              data +
              '<span class="msg_time"> '+ time +' </span></div></div>'
            );
            $("#message-body").animate(
              { scrollTop: $("#message-body")[0].scrollHeight },
              1000
            );
          } else {
            // Başarısız sonuçlanan Backend fonksiyonu response değeri
            console.log(response);
          }
        },
        // Başarısız sonuçlanan AJAX fonksiyonu
        error: function (e) {
          console.log("Ajax Post İsteği Hatası");
        },
      });
      event.preventDefault();
    }
  });
});

// QR kod upload fonksiyonu
$(document).ready(function (e) {
  $("#upload-button").click(function (e) {
    var file_data = $("#input_field").prop("files")[0]; // #input_field id'sine sahip elementten yüklenen dosyanın alınması
    var form_data = new FormData(); // FormData class'ından obje oluşturulması
    form_data.append("file", file_data); // Objenin içerisine yüklenen dosyanın atılması

    e.preventDefault();
    // QR kodun API hizmet sağlayıcısına AJAX ile post atılması
    $.ajax({
      url: "http://api.qrserver.com/v1/read-qr-code/",
      type: "POST",
      data: form_data,
      contentType: false,
      cache: false,
      processData: false,
      // Başarılı gerçekleşen POST işlem fonksiyonu
      success: function (response) {
        if (response[0].symbol[0].error == null) {
          var today = new Date();
          //var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
          var time = today.getHours() + ":" + today.getMinutes();
          //var dateTime = date+' | '+time;
          var data = response[0].symbol[0].data;
          // ---------------------------------------------------
          // API'den gelen QR kod içeriğinin, uygulama backend kısmına AJAX ile POST atılması
          $.ajax({
            data: {
              qr: data,
            },
            type: "POST",
            url: "/qr_upload",
            // Başarılı gerçekleşen POST işlem fonksiyonu
            success: function (response) {
              // Backend'den gelen cevabın ekrana basılması
              $("#message-body").append(
                '<div class="d-flex justify-content-start mb-4">' +
                '<div class="img_cont_msg">' +
                '<img src="https://avatars3.githubusercontent.com/u/68184733?s=200&v=4" class="rounded-circle user_img_msg">' +
                '</div><div class="msg_cotainer">' +
                response +
                '<span class="msg_time"> '+ time +' </span></div></div>'
              );
              $("#message-body").animate(
                { scrollTop: $("#message-body")[0].scrollHeight },
                1000
              );
              $("#message_text").val("");
            },
            // Başarısız gerçekleşen Backend POST fonksiyonu
            error: function (e) {
              console.log("Backend QR İletişim Hatası");
            },
          });
          // ---------------------------------------------------
          // Başarısız gerçekleşen API POST işlem fonksiyonu
        } else {
          console.log(response[0].symbol[0].error);
        }
      },
      // Başarısız gerçekleşen AJAX POST işlem fonksiyonu
      error: function (e) {
        console.log(e)
      },
    });
    $("#upload-button").css("display", "none");
  });
});

// Bot Konuşması Display Özelliği
$(document).ready(function () {
  $("#bot").click(function () {
    $("#message-body-2").css("display", "none");
    $("#message-body").css("display", "block");
    $("#bot").addClass("active");
    $("#eserler").removeClass("active");
    $("#message_text").prop("disabled", false);
    $("#input_field").prop("disabled", false);
  });
});

// Eserler Konuşması Display Özelliği
$(document).ready(function () {
  $("#eserler").click(function () {
    $("#message-body").css("display", "none");
    $("#message-body-2").css("display", "block");
    $("#bot").removeClass("active");
    $("#eserler").addClass("active");
    $("#message_text").prop("disabled", true);
    $("#input_field").prop("disabled", true);
  });
});



// Enter İle Send Messsage Trigger Özelliği
$(document).ready(function () {
$("#message_text").keypress(function (e) {
  if (e.keyCode == 13 && !e.shiftKey) {
    e.preventDefault();
    $("#btnSubmit").trigger("click");
  }
});
});