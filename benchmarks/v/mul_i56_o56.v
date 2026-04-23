module mul_i56_o56 (a, b, r);
input [27:0] a,b;
output [55:0] r;

assign r = a * b;

endmodule
