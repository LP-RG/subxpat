module madd_i123_o82 (a, b, c, r);
input [40:0] a,b,c;
output [81:0] r;

assign r = (a * b) + c;

endmodule
