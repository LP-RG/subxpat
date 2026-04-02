module madd_i339_o226 (a, b, c, r);
input [112:0] a,b,c;
output [225:0] r;

assign r = (a * b) + c;

endmodule
