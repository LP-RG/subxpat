module mul_i448_o448 (a, b, r);
input [223:0] a,b;
output [447:0] r;

assign r = a * b;

endmodule
