//document.write('<script src="../../../AV/Development/formal_language/fa/FA.js"></script>');
$(document).ready(function() {
  "use strict";

  var av_name = "DFA_withTrapStateCON";
  var av = new JSAV(av_name, {animationMode: "none"});
  var xPosition = 375;
  var yPosition = 10;
  var length1 = 125;
  var width = 30;
  var BinaryDFA = new av.ds.fa();
  var q0 = BinaryDFA.addNode({left: 50, top: 50});
  var q1 = BinaryDFA.addNode({left: 150, top: 50});
  var q2 = BinaryDFA.addNode({left: 250, top: 50});
  var trap = BinaryDFA.addNode({left: 150, top: 150});
  trap.value("trap");
  BinaryDFA.disableDragging();
  toggleInitial(BinaryDFA, q0);
  toggleFinal(BinaryDFA, q2);
  BinaryDFA.addEdge(q0, q1, {weight: "b"});
  BinaryDFA.addEdge(q1, q1, {weight: "b"});
  BinaryDFA.addEdge(q1, q2, {weight: "a"});
  BinaryDFA.addEdge(q0, trap, {weight: "a"});
  BinaryDFA.addEdge(q2, trap, {weight: "a, b"});
  //BinaryDFA.addEdge(q2, trap, {weight: "b"});
  BinaryDFA.addEdge(trap, trap, {weight: "a, b"});
  //BinaryDFA.addEdge(trap, trap, {weight: "b"});
  BinaryDFA.layout();
  av.displayInit();
  av.recorded();
});