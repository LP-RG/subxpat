module madd_i45_o30 (a, b, c, r);
input [14:0] a,b,c;
output [29:0] r;

assign r = (a * b) + c;

endmodule
