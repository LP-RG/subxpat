module madd_i6912_o4608 (a, b, c, r);
input [2303:0] a,b,c;
output [4607:0] r;

assign r = (a * b) + c;

endmodule
