module mul_i256_o256 (a, b, r);
input [127:0] a,b;
output [255:0] r;

assign r = a * b;

endmodule
