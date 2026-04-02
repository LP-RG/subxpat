module buttfly_i48_o50 (a,b,r1,r2);
input [23:0] a,b;
output [24:0] r1,r2;

assign r1 = a+b;

assign r2 = a-b;

endmodule
