module madd_i159_o106 (a, b, c, r);
input [52:0] a,b,c;
output [105:0] r;

assign r = (a * b) + c;

endmodule
