module mul_i52_o52 (a, b, r);
input [25:0] a,b;
output [51:0] r;

assign r = a * b;

endmodule
