module mul_i200_o200 (a, b, r);
input [99:0] a,b;
output [199:0] r;

assign r = a * b;

endmodule
