module mul_i44_o44 (a, b, r);
input [21:0] a,b;
output [43:0] r;

assign r = a * b;

endmodule
