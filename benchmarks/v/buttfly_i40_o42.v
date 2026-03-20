module buttfly_i40_o42 (a,b,r1,r2);
input [19:0] a,b;
output [20:0] r1,r2;

assign r1 = a+b;
assign r2 = a-b;

endmodule
