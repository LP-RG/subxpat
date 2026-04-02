module madd_i318_o212 (a, b, c, r);
input [105:0] a,b,c;
output [211:0] r;

assign r = (a * b) + c;

endmodule
