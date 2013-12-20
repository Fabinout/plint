function showCustom(a) {
  if (a) {
    document.getElementById("custom_template").style.display = "block";
  } else {
    document.getElementById("custom_template").style.display = "none";
  }
}

/*
// http://stackoverflow.com/questions/13240310/how-to-enforce-li-formatting-in-a-contenteditable-ul
//keyup prevented the user from deleting the bullet (by adding one back right after delete), but didn't add in li's on empty ul's, thus keydown added to check
// TODO make this work
// TODO fix border problems
function setevt() {
  $('#poem').on('keyup keydown', function() {
    var $this = $(this);
      if (! $this.find('li').length == 0) {
          var $li = $('&lt;li&gt;&lt;/li&gt;');
          var sel = window.getSelection();
         var range = sel.getRangeAt(0);
          range.collapse(false);
          range.insertNode($li.get(0));
          range = range.cloneRange();
          range.selectNodeContents($li.get(0));
          range.collapse(false);
          sel.removeAllRanges();
          sel.addRange(range);

      } else {
          //are there any tags that AREN'T LIs?
          //this should only occur on a paste
          var $nonLI = $this.find(':not(li, br)');

          if ($nonLI.length) {
              $this.contents().replaceWith(function() {
      //we create a fake div, add the text, then get the html in order to strip out html code. we then clean up a bit by replacing nbsp's with real spaces
  return '&lt;li&gt;' + $('&lt;div /&gt;').text($(this).text()).html().replace(/&nbsp;/g, ' ') + '</li>';
              });
              //we could make this better by putting the caret at the end of the last LI, or something similar
          }                   
      }
  });
};

*/

// http://stackoverflow.com/questions/13240310/how-to-enforce-li-formatting-in-a-contenteditable-ul
//keyup prevented the user from deleting the bullet (by adding one back right after delete), but didn't add in li's on empty ul's, thus keydown added to check
$( document ).ready(function() {
  console.log("SETUP");

  /*
  $('#poem').on('keyup keydown paste', function() {
      //are there any tags that AREN'T LIs?
      //this should only occur on a paste
      var $nonLI = $this.find(':not(li, br)');

      if ($nonLI.length) {
          $this.contents().replaceWith(function() {
  //we create a fake div, add the text, then get the html in order to strip out html code. we then clean up a bit by replacing nbsp's with real spaces
return '&lt;li&gt;' + $('&lt;div /&gt;').text($(this).text()).html().replace(/&nbsp;/g, ' ') + '</li>';
          });
          //we could make this better by putting the caret at the end of the last LI, or something similar
      }                   
  });
  
*/
  $('#poem').on('paste', function() {

    console.log("AHA");

    object.saveCursorPosition(); // TODO
    var textarea= $("<div contenteditable></div>");
    textarea.css("position",  "absolute").css("left", "-1000px").css("top", object.$editable.offset().top + "px").attr("id","pasteHelper").appendTo("body");
    textarea.html('<BR>');
    textarea.focus();

    setTimeout(function() {
        object.$editable.focus();
        object.restoreCursorPosition();
        object.insertTextAtCursor(textarea.text());
        textarea.remove();
    }, 0);
  });
});

function check() {
  // TODO handle errors
  $( "#poem" ).find('span').remove()
  $( "#poem" ).contenteditable = false;
  $( "#status" ).html("Checking...");
  console.log($( "#poem" ).html());
  var clone = $( "#poem" ).clone();
  clone.find(":not(br)").remove().end().html();
  clone.find("br").replaceWith("\n");
  var poem = clone.text();
  // TODO change errors in place
  // TODO remove all errors
  // TODO better error integration
  // TODO template selection
  // TODO page exit confirmation
  $.ajax({
    url: "checkjs",
    type: "post",
    data: {
      'template': $( "#user_template" ).val(),
     // 'poem': $( "#poem" ).contents().map(function() {
     //   return $(this).text();
     // }).get().join('\n')
     // http://stackoverflow.com/questions/3442394/jquery-using-text-to-retrieve-only-text-not-nested-in-child-tags
      'poem': poem
    },
    success: function (data) {
      if ("error" in data) {
        $( "#status" ).html("error: " + data.error);
//        $( "#poem li").each(function() {
//          $(this).css({'color': 'black'});
//        });
//      $
      } else {
        for (var i = data.result.length - 1; i >= 0; i--) {
          if (data.result[i][1].length > 0) {
            $( "#poem > br:nth-child(" + (i) + ")" ).before(" <span contenteditable=\"false\"><button>Toggle errors</button><pre>" + data.result[i][1] + "</pre></span>");
            //$( "#poem li:nth-child(" + (i) + ")" ).css({'color': 'red'});
          }
        }
        $( "#status" ).html("checked: nerror " + data.nerror);
      }
      $( "#poem" ).contenteditable = true;
     //  $( "#poem  ").find('pre').each(function() {
     //    $(this).css({'color': 'black'});
     //  });
      $('#poem button').on('click', function() {
        var old = $(this).parent().find('pre').css("display");
        var val;
        if (old == "none") {
          val = "block";
        } else {
          val = "none";
        }
        $(this).parent().find('pre').css({'display': val});
      });
    }
    });
}


/*
// http://stackoverflow.com/questions/2176861/javascript-get-clipboard-data-on-paste-event-cross-browser
function handlepaste (elem, e) {
    var savedcontent = elem.innerHTML;
    if (e && e.clipboardData && e.clipboardData.getData) {// Webkit - get data from clipboard, put into editdiv, cleanup, then cancel event
        if (/text\/html/.test(e.clipboardData.types)) {
            elem.innerHTML = e.clipboardData.getData('text/html');
        }
        else if (/text\/plain/.test(e.clipboardData.types)) {
            elem.innerHTML = e.clipboardData.getData('text/plain');
        }
        else {
            elem.innerHTML = "";
        }
        waitforpastedata(elem, savedcontent);
        if (e.preventDefault) {
                e.stopPropagation();
                e.preventDefault();
        }
        return false;
    }
    else {// Everything else - empty editdiv and allow browser to paste content into it, then cleanup
        elem.innerHTML = "";
        waitforpastedata(elem, savedcontent);
        return true;
    }
}

function waitforpastedata (elem, savedcontent) {
    if (elem.childNodes && elem.childNodes.length > 0) {
        processpaste(elem, savedcontent);
    }
    else {
        that = {
            e: elem,
            s: savedcontent
        }
        that.callself = function () {
            waitforpastedata(that.e, that.s)
        }
        setTimeout(that.callself,20);
    }
}

function processpaste (elem, savedcontent) {
    pasteddata = elem.innerHTML;
    //^^Alternatively loop through dom (elem.childNodes or elem.getElementsByTagName) here

    elem.innerHTML = savedcontent;

    // Do whatever with gathered data;
    $("#poem").text(pasteddata);
}

*/
