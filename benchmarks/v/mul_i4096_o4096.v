module mul_i4096_o4096 (a, b, r);
input [2047:0] a,b;
output [4095:0] r;

assign r = a * b;

endmodule
