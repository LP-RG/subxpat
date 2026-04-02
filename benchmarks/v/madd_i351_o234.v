module madd_i351_o234 (a, b, c, r);
input [116:0] a,b,c;
output [233:0] r;

assign r = (a * b) + c;

endmodule
