$(".about-bar").click(function() {
  $expandable = $(this);
  $content = $expandable.next();
  $content.slideToggle(500, function() {
    $expandable.text(function() {
      return $content.is(":visible") ? "Close" : "About";
    });
  });
});

$("#cal").attr('type', 'date');