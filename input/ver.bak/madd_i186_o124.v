module madd_i186_o124 (a, b, c, r);
input [61:0] a,b,c;
output [123:0] r;

assign r = (a * b) + c;

endmodule
