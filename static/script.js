function showCustom(a) {
  if (a) {
    document.getElementById("custom_template").style.display = "block";
  } else {
    document.getElementById("custom_template").style.display = "none";
  }
}

function check() {
  $( "#status" ).html("Checking...")
  $.ajax({
    url: "checkjs",
    type: "post",
    data: {
      'template': $( "#custom_template" ).val(),
      'poem': $( "#poem" ).text()
    },
    success: function (data) {
      if ("error" in data) {
        $( "#status" ).html("error: " + data.error);
      } else {
        $( "#status" ).html("checked: nerror " + data.nerror);
        $( "#result" ).html(data.result);
      }
    }
    });
}

