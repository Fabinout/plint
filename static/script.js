/* http://chrissilich.com/blog/convert-em-size-to-pixels-with-jquery/ */
function em2px(n) {
    var emSize = parseFloat($("body").css("font-size"));
    return (emSize * n);
}

function htmlentities(x) {
  return $('<div/>').text(x).html();
}

function onlydigits(x) {
  return String(x).replace(/[^0-9]/, '');
}

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

function getAvail() {
  var avail = $( window ).height() - $( '#lcontainer' ).offset().top - em2px(4) - $( '#tools' ).height() - $( '#predef' ).height();
  if ($( '#user_template' ).is(":visible")) {
    avail -= em2px(.5);
  }
  if ($( window ).width() <= 650) {
    avail -= em2px(1);
  }
  return avail;
}

function sanitize(e) {
  var avail = getAvail();
  var h1 = $( '#poem' ).height();
  var h2 = $( '#user_template' ).height();
  var h3 = $( '#cerrors' ).height();
  if (h1 > avail) {
    $( '#poem' ).height(avail);
    h1 = avail;
  }
  if (h2 > avail) {
    $( '#user_template' ).height(avail);
    h2 = avail;
  }
  if (h3 > avail) {
    $( '#cerrors' ).height(avail);
    h3 = avail;
  }
}

function resizeCErrors(e) {
  if ($( window ).width() > 650) {
    /* stretch cerrors */
    $( '#cerrors' ).height($( window ).height() - $( '#cerrors' ).offset().top - em2px(1));
  }
}

function resizeAllPoem(e) {
  sanitize(e);
  var avail = getAvail();
  var h1 = $( '#poem' ).height();
  avail -= h1;
  var h2 = $( '#user_template' ).height();
  var h3 = $( '#cerrors' ).height();
  if (!($( '#user_template' ).is(":visible")) && ($( window ).width() > 650)) {
    /* silly, just take the entire height */
    $( '#poem' ).height(avail + h1);
  } else {
    if ($( window ).width() <= 650) {
      /* fix user_template, use the rest for cerrors*/
      if ($( '#user_template' ).is(":visible")) {
        avail -= h2;
      }
      $( '#cerrors' ).height(0.1 + avail);
    } else {
      /* use the rest for user_template */
      $( '#user_template' ).height(0.1 + avail);
    }
  }
  resizeCErrors(e);
}

function resizeAllUserTemplate(e) {
  sanitize(e);
  var avail = getAvail();
  var h1 = $( '#poem' ).height();
  var h2 = $( '#user_template' ).height();
  var h3 = $( '#cerrors' ).height();
  avail -= h2;
  /* share what remains among other elements */
  var used = h1 + 0.01;
  if ($( window ).width() <= 650) {
    used += h3;
  }
  $( '#poem' ).height(h1 * avail/used);
  if ($( window ).width() <= 650) {
    $( '#cerrors' ).height(0.1 + h3 * avail/used);
  }
  resizeCErrors(e);
}

function resizeAll(e) {
  sanitize(e);
  var avail = getAvail();
  var h1 = $( '#poem' ).height();
  var h2 = $( '#user_template' ).height();
  var h3 = $( '#cerrors' ).height();
  /* just scale existing proportions */
  var used = h1 + 0.01;
  if ($( '#user_template' ).is(":visible")) {
    used += h2;
  }
  if ($( window ).width() <= 650) {
    used += h3;
  }
  $( '#poem' ).height(h1 * avail/used);
  if ($( '#user_template' ).is(":visible")) {
    $( '#user_template' ).height(0.1 + h2 * avail/used);
  }
  if ($( window ).width() <= 650) {
    $( '#cerrors' ).height(0.1 + h3 * avail/used);
  }
  resizeCErrors(e);
}

window.onresize = resizeAll;
window.onload = resizeAll;

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
      reportError(htmlentities(stat) +
         (error.length > 0 ? ": " + htmlentities(error) : ""));
      $('#check').prop( "disabled", false);
      // do not keep old errors around lest the user may miss the problem
      $( "#errors" ).empty();
    },
    success: function (data) {
      if ("error" in data) {
        $( "#status" ).html("<span class=\"error\">" + htmlentities(data.error) + "</span>");
        $( "#errors" ).empty();
      } else {
        $( "#errors" ).empty();
        for (var i = 0; i < data.result.length; i++) {
          var err = data.result[i];
          for (var j = 0; j < err.errors.length; j++) {
            err.errors[j] = htmlentities(err.errors[j]);
          }
          $( "#errors" ).append("<li onclick=\"gotoLine(" + onlydigits(err.num) + ")\">" +
            "<p>" + (lang == "fr"
              ? "Erreurs pour la ligne "
              : "Errors for line ")
            + onlydigits(err.num) + ":</p>" +
            "<blockquote>" + htmlentities(err.line) + "</blockquote>" +
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
      reportError(htmlentities(stat) +
          (error.length > 0 ? ": " + htmlentities(error) : ""));
    },
    success: function (data) {
      $( '#user_template' ).val(htmlentities(data));
      $('#user_template').show();
      $('#customize').prop("disabled", true);
      resizeAll();
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
  resizeAll();
}

function gotoLine(l) {
  var pos = 0;
  var lines = $( '#poem' ).val().split('\n');
  for (var i = 0; i < l - 1; i++)
    pos += lines[i].length + "\n".length;
  $( '#poem' ).caretTo(pos);
}

/* http://stackoverflow.com/a/7055239 */
jQuery(document).ready(function(){
   $( '#user_template' ).mouseup(function(){
     resizeAllUserTemplate();
   });
   $( '#user_template' ).dblclick(function(){
     resizeAllUserTemplate();
   });
   $( '#poem' ).mouseup(function(){
     resizeAllPoem();
   });
   $( '#poem' ).dblclick(function(){
     resizeAllPoem();
   });
   resizeAll();
  setTimeout(function () {
        $(window).resize();
  }, 1000);
});

$(document).load(function(e) {
  setTimeout(function () {
        $(window).resize();
  }, 1000);
});

