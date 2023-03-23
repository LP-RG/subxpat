module top(pi0, pi1, pi2, pi3, po0, po1);
  input pi0, pi1, pi2, pi3;
  output po0, po1;
  wire n5, n6, n7, n8, n9, n10, n11, n12;
  assign n5 = pi0 & ~pi2;
  assign n6 = ~pi0 & pi2;
  assign n7 = ~n5 & ~n6;
  assign n8 = pi1 & ~pi3;
  assign n9 = ~n6 & n8;
  assign n10 = ~pi1 & pi3;
  assign n11 = ~n5 & n10;
  assign n12 = ~n9 & ~n11;
  assign po0 = ~n7;
  assign po1 = ~n12;
endmodule
