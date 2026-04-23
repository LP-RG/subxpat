module mul_i120_o120 (a, b, r);
input [59:0] a,b;
output [119:0] r;

assign r = a * b;

endmodule
