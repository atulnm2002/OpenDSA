"use strict";
$(document).ready(function () {
    const Match =  2;
    const Mismatch =-3;
    const Gap =  -6;
    var s1="AACG";
    var s2="ACTCG"
    var jsav = new JSAV("LExercise");
    var Frames = PIFRAMES.init("LExercise");
    jsav.umsg("Match = 2, Mismatch = -3, Gap = -6");
    var matrix = new jsav.ds.matrix([[,,"A" ,"C" , "T","G" ,"C","T","G"],["","","" ,"" , "","" ,"","",""],["A","","" ,"" , "","" ,"","",""],["C","","" ,"" , "","" ,"","",""]
    ,["T","","" ,"" , "","" ,"","",""],["G","","" ,"" , "","" ,"","",""],["A","","" ,"" , "","" ,"","",""],["C","","" ,"" , "","" ,"","",""]], 
    {style: "table", top: 0, left: 200});
    matrix.value(1,1,0);
    jsav.displayInit();
    matrix.value(1,2,0);
    jsav.step();
    matrix.value(1,3,0);
    jsav.umsg(Frames.addQuestion("1"));
    jsav.step();
    matrix.value(1,4,0);
    jsav.step();
    matrix.value(1,5,0);
    jsav.step();
    matrix.value(1,6,0);
    jsav.step();
    matrix.value(1,7,0);
    jsav.step();
    matrix.value(1,8,0);
    jsav.step();
    matrix.value(2,1,0);
    jsav.step();
    matrix.value(3,1,0);
    jsav.step();
    matrix.value(4,1,0);
    jsav.step();
    matrix.value(5,1,0);
    jsav.step();
    matrix.value(6,1,0);
    jsav.step();
    matrix.value(7,1,0);
    jsav.step();
    matrix.value(2,2,2);
    jsav.step();
    matrix.value(2,3,0);
    jsav.step();
    matrix.value(2,4,0);
    jsav.step();
    matrix.value(2,5,0);
    jsav.step();
    matrix.value(2,6,0);
    jsav.step();
    matrix.value(2,7,0);
    jsav.step();
    matrix.value(2,8,0);
    jsav.step();
    matrix.value(3,2,0);
    jsav.step();
    matrix.value(3,3,4);
    jsav.step();
    matrix.value(3,4,0);
    jsav.step();
    matrix.value(3,5,0);
    jsav.step();
    matrix.value(3,6,2);
    jsav.step();
    matrix.value(3,7,0);
    jsav.step();
    matrix.value(3,8,0);
    jsav.step();
    matrix.value(4,2,0);
    jsav.step();
    matrix.value(4,3,0);
    jsav.step();
    matrix.value(4,4,6);
    jsav.step();
    matrix.value(4,5,0);
    jsav.step();
    matrix.value(4,6,0);
    jsav.step();
    matrix.value(4,7,4);
    jsav.step();
    matrix.value(4,8,0);
    jsav.step();
    matrix.value(5,2,0);
    jsav.step();
    matrix.value(5,3,0);
    jsav.step();
    matrix.value(5,4,0);
    jsav.step();
    matrix.value(5,5,8);
    jsav.step();
    matrix.value(5,6,2);
    jsav.step();
    matrix.value(5,7,0);
    jsav.step();
    matrix.value(5,8,6);
    jsav.step();
    matrix.value(6,2,2);
    jsav.step();
    matrix.value(6,3,0);
    jsav.step();
    matrix.value(6,4,0);
    jsav.step();
    matrix.value(6,5,2);
    jsav.step();
    matrix.value(6,6,5);
    jsav.step();
    matrix.value(6,7,0);
    jsav.step();
    matrix.value(6,8,0);
    jsav.step();
    matrix.value(7,2,0);
    jsav.step();
    matrix.value(7,3,4);
    jsav.step();
    matrix.value(7,4,0);
    jsav.step();
    matrix.value(7,5,0);
    jsav.step();
    matrix.value(7,6,4);
    jsav.step();
    matrix.value(7,7,2);
    jsav.step();
    matrix.value(7,8,0);
    matrix.layout();
	jsav.recorded();
})