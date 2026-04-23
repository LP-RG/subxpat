module madd_i10752_o7168 (a, b, c, r);
input [3583:0] a,b,c;
output [7167:0] r;

assign r = (a * b) + c;

endmodule
