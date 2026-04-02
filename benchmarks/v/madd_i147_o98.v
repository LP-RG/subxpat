module madd_i147_o98 (a, b, c, r);
input [48:0] a,b,c;
output [97:0] r;

assign r = (a * b) + c;

endmodule
