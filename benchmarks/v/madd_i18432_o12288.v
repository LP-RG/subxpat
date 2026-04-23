module madd_i18432_o12288 (a, b, c, r);
input [6143:0] a,b,c;
output [12287:0] r;

assign r = (a * b) + c;

endmodule
