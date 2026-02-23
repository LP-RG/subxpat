module mul_i80_o80 (a, b, r);
input [39:0] a,b;
output [79:0] r;

assign r = a * b;

endmodule
