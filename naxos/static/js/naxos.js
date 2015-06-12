// regex
// http://james.padolsey.com/javascript/regex-selector-for-jquery/
jQuery.expr[':'].regex = function(elem, index, match) {
var matchParams = match[3].split(','),
    validLabels = /^(data|css):/,
    attr = {
        method: matchParams[0].match(validLabels) ? 
                    matchParams[0].split(':')[0] : 'attr',
        property: matchParams.shift().replace(validLabels,'')
    },
    regexFlags = 'ig',
    regex = new RegExp(matchParams.join('').replace(/^\s+|\s+$/g,''), regexFlags);
return regex.test(jQuery(elem)[attr.method](attr.property));
};

// Scroll to caret position in a text field
function scrollToPosition($textarea, caret) {
    var text = $textarea.val();
    var textBeforePosition = text.substring(0, caret);
    $textarea.blur();
    $textarea.val(textBeforePosition);
    $textarea.focus();
    $textarea.val(text);
    $textarea[0].setSelectionRange(caret, caret);
};

// Document ready jquery
$(document).ready(function(){

  // Ensure author div and content div stay the same size
  // supporting code in grid.js
  $('.equal-divs').responsiveEqualHeightGrid();
  // Ensure presentation is ok while media still loading
  var x = setInterval(function() {
    $('.equal-divs').responsiveEqualHeightGrid();
  }, 500);
  $(window).load(function() {
    // Stops presentation refresh when everything loaded
    clearInterval(x);
  });

  // Responsive images in posts
  $('.post-content img').load(function() {
      if ($(this).width() > 100) {
        $(this).addClass("img-responsive");
      }
  });

  // Remove inner spoiler tags
  $(".panel-body .panel").remove();

  // Remove inner quotes
  $("blockquote blockquote").remove();

  // Animate poll results
  var $chart = $('.poll-chart');
  var $bar = $('.poll-bar');
  var highestNumber = 0;  
  var sum = 0;
  // Get highest number and use that as 100%
  $chart.find($bar).each(function() {
      var num = parseInt($(this).text(),10);
      sum += num;
      if (num > highestNumber) {
          highestNumber = num;
      };
  });
  // Set the progress bar data
  $chart.find($bar).each(function() {
      num = $(this).text();
      // Convert to percentage and round
      dispPerc = Math.round((num / highestNumber) * 100);
      realPerc = Math.round((num / sum) * 100);
      if(!isNaN(realPerc) && realPerc !== 0) {
          $(this).animate({width: dispPerc + '%'}, {duration:'fast'});
          $(this).text(Math.round(realPerc) + '%');
          $(this).attr("aria-valuenow", dispPerc);
      } else {
          $(this).text("");
      };
  });

  // Ensure presentation is ok while spoiler animation is playing
  // Give spoiler tags unique ids and hyperlink adresses
  $("div[id^='spoiler-panel']").attr("id", function(index) {
    return 'spoiler-panel-' + (index+1);
  });
  $("a[href^='#spoiler-panel']").attr("href", function(index) {
    return '#spoiler-panel-' + (index+1);
  });
  $("a[href^='#spoiler-panel-']").click(function() {
    $spoiler = $(this);
    var spoiler_anim = setInterval(function() {
      $container = $spoiler.parents('.spoiler-container');
      $container.children("div[id^='spoiler-panel-']").on('shown.bs.collapse', function() {
        clearInterval(spoiler_anim);
      });
      $container.children("div[id^='spoiler-panel-']").on('hidden.bs.collapse', function() {
        clearInterval(spoiler_anim);
      });
      $row = $spoiler.parents('.row');
      $row.children('.equal-divs').responsiveEqualHeightGrid();
    }, 20);
  });

});

// socket.io
$(document).ready(function(){
  var socket = io('http://geekattitude.org:80');
  $(window).on('beforeunload', function(){
    socket.close();
  });
});
