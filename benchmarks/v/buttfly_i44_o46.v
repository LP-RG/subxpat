module buttfly_i44_o46 (a,b,r1,r2);
input [21:0] a,b;
output [22:0] r1,r2;

assign r1 = a+b;

assign r2 = a-b;

endmodule
