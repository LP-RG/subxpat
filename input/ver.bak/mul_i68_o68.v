module mul_i68_o68 (a, b, r);
input [33:0] a,b;
output [67:0] r;

assign r = a * b;

endmodule
