module buttfly_i16_o18 (a,b,r1,r2);
input [7:0] a,b;
output [8:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
