module buttfly_i36_o38 (a,b,r1,r2);
input [17:0] a,b;
output [18:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
