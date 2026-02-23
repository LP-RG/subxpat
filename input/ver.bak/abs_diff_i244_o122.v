module abs_diff_i244_o122(a,b,r);
input [121:0] a,b;
output [121:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
