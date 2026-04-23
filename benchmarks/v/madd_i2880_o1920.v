module madd_i2880_o1920 (a, b, c, r);
input [959:0] a,b,c;
output [1919:0] r;

assign r = (a * b) + c;

endmodule
