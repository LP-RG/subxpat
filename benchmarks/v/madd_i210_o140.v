module madd_i210_o140 (a, b, c, r);
input [69:0] a,b,c;
output [139:0] r;

assign r = (a * b) + c;

endmodule
