module abs_diff_i30_o15(a,b,r);
input [14:0] a,b;
output [14:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
