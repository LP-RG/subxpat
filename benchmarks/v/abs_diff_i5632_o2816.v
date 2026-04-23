module abs_diff_i5632_o2816(a,b,r);
input [2815:0] a,b;
output [2815:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
