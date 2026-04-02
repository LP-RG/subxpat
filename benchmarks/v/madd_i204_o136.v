module madd_i204_o136 (a, b, c, r);
input [67:0] a,b,c;
output [135:0] r;

assign r = (a * b) + c;

endmodule
