module abs_diff_i14336_o7168(a,b,r);
input [7167:0] a,b;
output [7167:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
