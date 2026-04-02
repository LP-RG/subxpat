module madd_i366_o244 (a, b, c, r);
input [121:0] a,b,c;
output [243:0] r;

assign r = (a * b) + c;

endmodule
