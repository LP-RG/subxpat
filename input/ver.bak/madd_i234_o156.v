module madd_i234_o156 (a, b, c, r);
input [77:0] a,b,c;
output [155:0] r;

assign r = (a * b) + c;

endmodule
