(function($) {

  var DisplayShortURL = function($widget) {

    var $input = $widget.find('input');
    $input.click(function(){
      $(this).select();
    });
  };

  $(document).ready(function(){

    $('.form-fields-container').live('loadwidget-smiform', function(event) {
      $.each($(this).find('div.display-shorturl-widget'), function(){
        DisplayShortURL($(this));
      });
    });

  });

})(jQuery);
