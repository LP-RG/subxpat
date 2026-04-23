module mul_i8192_o8192 (a, b, r);
input [4095:0] a,b;
output [8191:0] r;

assign r = a * b;

endmodule
