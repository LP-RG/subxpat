module mul_i2560_o2560 (a, b, r);
input [1279:0] a,b;
output [2559:0] r;

assign r = a * b;

endmodule
