"use strict";

$(document).ready(function () {
  var av_name = "Else";
  var config = ODSA.UTILS.loadConfig({av_name: av_name}),
  interpret = config.interpreter,       // get the interpreter
  code = config.code;  
  var jsav = new JSAV(av_name);

  var pseudo = jsav.code(code[0]);

  jsav.displayInit();
  jsav.umsg("First Enter the Try block and execute inside")
  pseudo.setCurrentLine(1);
  jsav.step();

  jsav.umsg("this line will execute and print without any error ")
  pseudo.unhighlight(1);
  pseudo.setCurrentLine(2);
  jsav.step();

  jsav.umsg(" Will continue to else block because of no error occured")
  pseudo.unhighlight(2);
  pseudo.setCurrentLine(5);
  jsav.step();
  jsav.umsg("print the statement in this block ")
  pseudo.unhighlight(5);
  pseudo.setCurrentLine(6);

  jsav.recorded();
});
