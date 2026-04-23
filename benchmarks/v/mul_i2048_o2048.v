module mul_i2048_o2048 (a, b, r);
input [1023:0] a,b;
output [2047:0] r;

assign r = a * b;

endmodule
