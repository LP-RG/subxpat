module madd_i30_o20 (a, b, c, r);
input [9:0] a,b,c;
output [19:0] r;

assign r = (a * b) + c;

endmodule
