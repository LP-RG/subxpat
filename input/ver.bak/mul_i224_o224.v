module mul_i224_o224 (a, b, r);
input [111:0] a,b;
output [223:0] r;

assign r = a * b;

endmodule
