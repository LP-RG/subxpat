module mul_i252_o252 (a, b, r);
input [125:0] a,b;
output [251:0] r;

assign r = a * b;

endmodule
