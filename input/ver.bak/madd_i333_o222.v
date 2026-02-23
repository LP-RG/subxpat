module madd_i333_o222 (a, b, c, r);
input [110:0] a,b,c;
output [221:0] r;

assign r = (a * b) + c;

endmodule
