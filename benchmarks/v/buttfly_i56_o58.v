module buttfly_i56_o58 (a,b,r1,r2);
input [27:0] a,b;
output [28:0] r1,r2;

assign r1 = a+b;

assign r2 = a-b;

endmodule
