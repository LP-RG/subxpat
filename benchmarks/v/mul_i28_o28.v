module mul_i28_o28 (a, b, r);
input [13:0] a,b;
output [27:0] r;

assign r = a * b;

endmodule
