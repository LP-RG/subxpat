module mul_i1280_o1280 (a, b, r);
input [639:0] a,b;
output [1279:0] r;

assign r = a * b;

endmodule
