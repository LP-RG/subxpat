module abs_diff_i660_o330(a,b,r);
input [329:0] a,b;
output [329:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
