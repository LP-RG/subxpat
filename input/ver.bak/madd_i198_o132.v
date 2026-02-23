module madd_i198_o132 (a, b, c, r);
input [65:0] a,b,c;
output [131:0] r;

assign r = (a * b) + c;

endmodule
