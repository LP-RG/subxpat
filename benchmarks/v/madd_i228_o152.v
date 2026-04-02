module madd_i228_o152 (a, b, c, r);
input [75:0] a,b,c;
output [151:0] r;

assign r = (a * b) + c;

endmodule
