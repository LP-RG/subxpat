module madd_i864_o576 (a, b, c, r);
input [287:0] a,b,c;
output [575:0] r;

assign r = (a * b) + c;

endmodule
