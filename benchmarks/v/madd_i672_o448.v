module madd_i672_o448 (a, b, c, r);
input [223:0] a,b,c;
output [447:0] r;

assign r = (a * b) + c;

endmodule
