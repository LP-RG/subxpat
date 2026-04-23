module madd_i33_o22 (a, b, c, r);
input [10:0] a,b,c;
output [21:0] r;

assign r = (a * b) + c;

endmodule
