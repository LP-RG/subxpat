module madd_i336_o224 (a, b, c, r);
input [111:0] a,b,c;
output [223:0] r;

assign r = (a * b) + c;

endmodule
