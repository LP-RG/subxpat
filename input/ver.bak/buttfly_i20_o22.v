module buttfly_i20_o22 (a,b,r1,r2);
input [9:0] a,b;
output [10:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
