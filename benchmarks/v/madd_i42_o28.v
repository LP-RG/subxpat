module madd_i42_o28 (a, b, c, r);
input [13:0] a,b,c;
output [27:0] r;

assign r = (a * b) + c;

endmodule
