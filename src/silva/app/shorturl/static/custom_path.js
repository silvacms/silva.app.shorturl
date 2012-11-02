(function($){

  var MaxFrequenceRunner = function(delay) {
    var timer = null;

    var clearTimer = function() {
      var oldTimer = timer;
      timer = null;
      if (oldTimer != null)
        clearTimeout(oldTimer);
    };

    return {
      run: function(runner) {
        clearTimer();
        timer = setTimeout(runner, delay);
      }
    };
  };

  var CustomPath = function($widget) {

    var $input = $widget.find('input');
    var $infoBox = $widget.find('.custom-path-info');
    var lookupURL = $input.attr('data-lookup-url');
    var intID = $input.attr('data-target-id');

    var validate = function(){
      var value = $input.val();
      if (value !== undefined && value != '') {
        $.getJSON(lookupURL + value, function(data){
          $infoBox.empty();
          if (data == null || data['intid'] == intID) {
            $infoBox.hide();
          } else {
            var content = $('<p>This short path is already bound to <a href="#settings!' + 
              data['path'] + '">' +
                '<img src="' + data['icon'] + '"/>' +
                data['title'] + "</a></p>" );
            $infoBox.append(content);
            $infoBox.show();
          }
        });
      }
    };

    var frequenceRun = new MaxFrequenceRunner(400);

    $input.bind('change keyup', function(){
      frequenceRun.run(validate);
    });

    return {};
  };

  $(document).ready(function(){

    $('.form-fields-container').live('loadwidget-smiform', function(event) {
      CustomPath($(this));
    });

  });

})(jQuery)
