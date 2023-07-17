module top(pi0, pi1, pi2, pi3, po0, po1, po2, po3);
  input pi0, pi1, pi2, pi3;
  output po0, po1, po2, po3;
  wire n5, n6, n7, n8, n9, n10, n11, n12;
  assign n5 = pi0 & pi2;
  assign n6 = pi1 & pi3;
  assign n7 = n5 & n6;
  assign n8 = pi0 & pi3;
  assign n9 = pi1 & pi2;
  assign n10 = ~n8 & ~n9;
  assign n11 = ~n7 & ~n10;
  assign n12 = ~n5 & n6;
  assign po0 = n5;
  assign po1 = n11;
  assign po2 = n12;
  assign po3 = n7;
endmodule
