module madd_i117_o78 (a, b, c, r);
input [38:0] a,b,c;
output [77:0] r;

assign r = (a * b) + c;

endmodule
