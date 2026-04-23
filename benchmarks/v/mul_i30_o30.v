module mul_i30_o30 (a, b, r);
input [14:0] a,b;
output [29:0] r;

assign r = a * b;

endmodule
