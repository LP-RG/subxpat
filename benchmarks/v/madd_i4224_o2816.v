module madd_i4224_o2816 (a, b, c, r);
input [1407:0] a,b,c;
output [2815:0] r;

assign r = (a * b) + c;

endmodule
