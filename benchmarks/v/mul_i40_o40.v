module mul_i40_o40 (a, b, r);
input [19:0] a,b;
output [39:0] r;

assign r = a * b;

endmodule
