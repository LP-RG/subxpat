module madd_i1728_o1152 (a, b, c, r);
input [575:0] a,b,c;
output [1151:0] r;

assign r = (a * b) + c;

endmodule
