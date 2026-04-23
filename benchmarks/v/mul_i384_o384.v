module mul_i384_o384 (a, b, r);
input [191:0] a,b;
output [383:0] r;

assign r = a * b;

endmodule
