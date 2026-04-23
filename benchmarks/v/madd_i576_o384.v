module madd_i576_o384 (a, b, c, r);
input [191:0] a,b,c;
output [383:0] r;

assign r = (a * b) + c;

endmodule
