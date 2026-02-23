module madd_i354_o236 (a, b, c, r);
input [117:0] a,b,c;
output [235:0] r;

assign r = (a * b) + c;

endmodule
