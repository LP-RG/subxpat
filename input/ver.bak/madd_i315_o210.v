module madd_i315_o210 (a, b, c, r);
input [104:0] a,b,c;
output [209:0] r;

assign r = (a * b) + c;

endmodule
