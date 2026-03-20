module buttfly_i28_o30 (a,b,r1,r2);
input [13:0] a,b;
output [14:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
