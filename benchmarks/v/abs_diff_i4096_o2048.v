module abs_diff_i4096_o2048(a,b,r);
input [2047:0] a,b;
output [2047:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
