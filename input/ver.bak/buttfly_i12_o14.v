module buttfly_i12_o14 (a,b,r1,r2);
input [5:0] a,b;
output [6:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
