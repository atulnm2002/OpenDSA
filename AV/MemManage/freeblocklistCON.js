$(document).ready(function () {
  "use strict";
  var av = new JSAV("freeblocklistCON", {"animationMode": "none"});
  var top = 30;
  var l = av.g.line(0, 30, 470, 30);
  var l2 = av.g.line(0, 80, 470, 80);
  
  var rect1 = av.g.rect(20, 30, 60, 50).css({"fill": "lightgray"});
  var rect2 = av.g.rect(80, 30, 70, 50).css({"fill": "white"});
  var rect3 = av.g.rect(150, 30, 100, 50).css({"fill": "lightgray"});
  var rect4 = av.g.rect(250, 30, 50, 50).css({"fill": "white"});
  var rect5 = av.g.rect(300, 30, 80, 50).css({"fill": "lightgray"});
  var rect6 = av.g.rect(380, 30, 40, 50).css({"fill": "white"});
  var rect7 = av.g.rect(420, 30, 30, 50).css({"fill": "lightgray"});
  
    
  //var point = av.pointer(xFrag, rect2);
  var xFragLabel = av.label("Used Block: Allocated memory", {left :  140, top:  -10});
  var xFragArrow = av.g.line(135, top - 15,  120, top, {'arrow-end': 'classic-wide-long', 'stroke-width' : 2});
  var inFragLabel = av.label("Free Block: Unallocated memory", {left :  140, top:  75});
  var inFragArrow = av.g.line(320, top + 65,  330, top + 50, {'arrow-end': 'classic-wide-long', 'stroke-width' : 2});
  
  av.displayInit();
  av.recorded();
});
