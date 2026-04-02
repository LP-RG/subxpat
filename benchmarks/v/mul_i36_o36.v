module mul_i36_o36 (a, b, r);
input [17:0] a,b;
output [35:0] r;

assign r = a * b;

endmodule
