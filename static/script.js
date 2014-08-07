function showCustom(a) {
  if (a) {
    document.getElementById("custom_template").style.display = "block";
  } else {
    document.getElementById("custom_template").style.display = "none";
  }
}

function reportError(msg) {
  if (lang == "fr") {
    var message = ("Impossible de vérifier le poème faute de pouvoir "
      + "communiquer avec le serveur&nbspp;: ");
  } else {
    var message = ("Could not check poem due to error when "
      + "communicating with server: ");
  }
  $( "#status" ).html("<span class=\"error\">" + message + msg + "</span>");
}

var setForCustom = false;

function setUnload() {
  window.onbeforeunload = function() {
    if (lang == "fr") {
      return ("Votre poème sera perdu en fermant cette page. "
          + "Êtes-vous sûr de vouloir la quitter ?");
    } else {
      return ("Your poem will be lost when closing this page. "
          + "Are you sure you want to navigate away?");
    }
  };
}

function toggleUnload() {
  if ($('#poem').val().length > 10) {
    setUnload();
  } else {
    if (!setForCustom) {
      window.onbeforeunload = null;
    }
  }
}

function setCustom() {
  setForCustom = true;
  setUnload();
}

function resizePoem(e) {
  $( '#poem' ).height(
      $( window ).height() - $( '#poem' ).offset().top - 20);
}

window.onresize = resizePoem;
window.onload = resizePoem;

function check() {
  $( "#status" ).html("Checking...");
  $('#check').prop( "disabled", true);
  var poem = $( '#poem' ).val();
  var mydata = {
      'poem': poem,
      'template': $( '#predef' ).val()
    };
  if (mydata['template'] == 'custom') {
    mydata['custom_template'] = $( "#user_template" ).val();
  }
  $.ajax({
    url: "checkjs",
    type: "post",
    data: mydata,
    error: function (jqxhr, stat, error) {
      reportError(stat + (error.length > 0 ? ": " + error : ""));
      $('#check').prop( "disabled", false);
      // do not keep old errors around lest the user may miss the problem
      $( "#errors" ).empty();
    },
    success: function (data) {
      if ("error" in data) {
        $( "#status" ).html("<span class=\"error\">" + data.error + "</span>");
      } else {
        $( "#errors" ).empty();
        for (var i = 0; i < data.result.length; i++) {
          var err = data.result[i];
          $( "#errors" ).append("<li onclick=\"gotoLine(" + err.num + ")\">" +
            "<p>" + (lang == "fr"
              ? "Erreurs pour la ligne "
              : "Errors for line ")
            + err.num + ":</p>" + 
            "<blockquote>" + err.line + "</blockquote>" +
            "<pre>" + err.errors.join("<br />") + "</pre></li>");
        }
        if (data.result.length > 0) {
          var agreement = (data.result.length == 1 ? "" : "s");
          var msg = data.result.length;
          if (lang == "fr") {
            msg += (" erreur" + agreement + " trouvée" + agreement
                + " en validant le poème&nbsp;!");
          } else {
            msg += (" error" + agreement
              + " found when validating poem" + "!");
          }
          $( "#status" ).html("<span class=\"error\">" + msg + "</span>");
        } else {
          if (lang == "fr") {
            var msg = "Poème conforme au modèle&nbsp;!";
          } else {
            var msg = "Poem validated against template!";
          }
          $( "#status" ).html("<span class=\"success\">" + msg + "</span>");
        }
      }
      $('#check').prop( "disabled", false);
    }
    });
}

function loadPredef() {
  var predef = $( '#predef' ).val();
  if (predef == "custom")
    return;
  $('#predef option[value="custom"]').prop('selected', true)
  $.ajax({
    url: "static/tpl/" + predef + ".tpl",
    type: "get",
    error: function (jqxhr, stat, error) {
      reportError(stat + (error.length > 0 ? ": " + error : ""));
    },
    success: function (data) {
      $( '#user_template' ).val(data);
      $('#user_template').show();
      $('#customize').prop("disabled", true);
      resizePoem();
    }
    });
  }

function toggleCustom() {
  if ($( '#predef' ).val() == 'custom') {
    $('#user_template').show();
    $('#customize').prop( "disabled", true);
  } else {
    $('#user_template').hide();
    $('#customize').prop("disabled", false);
  }
  resizePoem();
}

function gotoLine(l) {
  var pos = 0;
  var lines = $( '#poem' ).val().split('\n');
  for (var i = 0; i < l - 1; i++)
    pos += lines[i].length + "\n".length;
  $( '#poem' ).caretTo(pos);
}

