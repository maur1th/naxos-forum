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
/**
 * Javascript-Equal-Height-Responsive-Rows
 * https://github.com/Sam152/Javascript-Equal-Height-Responsive-Rows
 */
(function($){$.fn.equalHeight=function(){var heights=[];$.each(this,function(i,element){$element=$(element);var element_height;var includePadding=($element.css('box-sizing')=='border-box')||($element.css('-moz-box-sizing')=='border-box');if(includePadding){element_height=$element.innerHeight();}else{element_height=$element.height();}
heights.push(element_height);});this.css('height',Math.max.apply(window,heights)+'px');return this;};$.fn.equalHeightGrid=function(columns){var $tiles=this;$tiles.css('height','auto');for(var i=0;i<$tiles.length;i++){if(i%columns===0){var row=$($tiles[i]);for(var n=1;n<columns;n++){row=row.add($tiles[i+n]);}
row.equalHeight();}}
return this;};$.fn.detectGridColumns=function(){var offset=0,cols=0;this.each(function(i,elem){var elem_offset=$(elem).offset().top;if(offset===0||elem_offset==offset){cols++;offset=elem_offset;}else{return false;}});return cols;};$.fn.responsiveEqualHeightGrid=function(){var _this=this;function syncHeights(){var cols=_this.detectGridColumns();_this.equalHeightGrid(cols);}
$(window).bind('resize load',syncHeights);syncHeights();return this;};})(jQuery);
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
// Posts presentation
$(document).ready(function() {
  // Ensure presentation is ok on DOM ready().
  $('.equal-divs').responsiveEqualHeightGrid();
})
var x = setInterval(function() {
  // Ensure presentation is ok while media still loading.
  $('.equal-divs').responsiveEqualHeightGrid();
}, 500);
$(window).load(function() {
  // Stops presentation refresh when everything loaded.
  clearInterval(x);
});
// Responsive images in posts
$(document).ready(function() {
  $('.post-content > img').addClass(function(){
    if (this.clientWidth > 100) {
      return "img-responsive"
    };
  });
})
// Ensure presentation is ok while spoiler animation is playing.
$(document).ready(function(){
  // Give spoiler tags unique ids
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
