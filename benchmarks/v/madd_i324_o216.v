module madd_i324_o216 (a, b, c, r);
input [107:0] a,b,c;
output [215:0] r;

assign r = (a * b) + c;

endmodule
