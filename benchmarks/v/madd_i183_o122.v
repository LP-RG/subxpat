module madd_i183_o122 (a, b, c, r);
input [60:0] a,b,c;
output [121:0] r;

assign r = (a * b) + c;

endmodule
