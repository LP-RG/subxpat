module madd_i1440_o960 (a, b, c, r);
input [479:0] a,b,c;
output [959:0] r;

assign r = (a * b) + c;

endmodule
