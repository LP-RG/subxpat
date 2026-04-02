module abs_diff_i1020_o510(a,b,r);
input [509:0] a,b;
output [509:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
