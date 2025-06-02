module buttfly_i60_o62 (a,b,r1,r2);
input [29:0] a,b;
output [30:0] r1,r2;

assign r1 = a+b;

assign r2 = a-b;

endmodule
