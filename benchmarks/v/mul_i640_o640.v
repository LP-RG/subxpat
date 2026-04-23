module mul_i640_o640 (a, b, r);
input [319:0] a,b;
output [639:0] r;

assign r = a * b;

endmodule
