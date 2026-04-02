module madd_i222_o148 (a, b, c, r);
input [73:0] a,b,c;
output [147:0] r;

assign r = (a * b) + c;

endmodule
