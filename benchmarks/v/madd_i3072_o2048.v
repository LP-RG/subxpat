module madd_i3072_o2048 (a, b, c, r);
input [1023:0] a,b,c;
output [2047:0] r;

assign r = (a * b) + c;

endmodule
