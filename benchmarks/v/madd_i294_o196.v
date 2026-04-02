module madd_i294_o196 (a, b, c, r);
input [97:0] a,b,c;
output [195:0] r;

assign r = (a * b) + c;

endmodule
