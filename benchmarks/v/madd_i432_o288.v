module madd_i432_o288 (a, b, c, r);
input [143:0] a,b,c;
output [287:0] r;

assign r = (a * b) + c;

endmodule
