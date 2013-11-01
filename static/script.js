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
      'template': $( "#custom_template" ).val(),
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
            $( "#poem > br:nth-child(" + (i+1) + ")" ).before(" <span contenteditable=\"false\"><button>Toggle errors</button><pre>" + data.result[i][1] + "</pre></span>");
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


