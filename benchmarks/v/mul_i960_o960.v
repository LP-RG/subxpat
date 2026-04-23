module mul_i960_o960 (a, b, r);
input [479:0] a,b;
output [959:0] r;

assign r = a * b;

endmodule
