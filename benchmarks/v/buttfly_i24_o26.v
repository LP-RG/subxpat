module buttfly_i24_o26 (a,b,r1,r2);
input [11:0] a,b;
output [12:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
