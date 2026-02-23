module madd_i306_o204 (a, b, c, r);
input [101:0] a,b,c;
output [203:0] r;

assign r = (a * b) + c;

endmodule
