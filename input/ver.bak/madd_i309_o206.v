module madd_i309_o206 (a, b, c, r);
input [102:0] a,b,c;
output [205:0] r;

assign r = (a * b) + c;

endmodule
