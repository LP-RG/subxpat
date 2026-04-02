module mul_i100_o100 (a, b, r);
input [49:0] a,b;
output [99:0] r;

assign r = a * b;

endmodule
