module madd_i2304_o1536 (a, b, c, r);
input [767:0] a,b,c;
output [1535:0] r;

assign r = (a * b) + c;

endmodule
