$(".about-bar").click(function() {
  $expandable = $(this);
  $content = $expandable.next();
  $content.slideToggle(500, function() {
    $expandable.text(function() {
      return $content.is(":visible") ? "Close" : "About";
    });
  });
});

$("#regForm :input").prop("disabled", true);
$("#regFormSubBut").prop("disabled", true);