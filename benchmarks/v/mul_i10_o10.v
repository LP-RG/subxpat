module mul_i10_o10 (a, b, r);
input [4:0] a,b;
output [9:0] r;

assign r = a * b;

endmodule
