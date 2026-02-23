module madd_i171_o114 (a, b, c, r);
input [56:0] a,b,c;
output [113:0] r;

assign r = (a * b) + c;

endmodule
