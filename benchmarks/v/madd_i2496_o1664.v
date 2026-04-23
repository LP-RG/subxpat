module madd_i2496_o1664 (a, b, c, r);
input [831:0] a,b,c;
output [1663:0] r;

assign r = (a * b) + c;

endmodule
