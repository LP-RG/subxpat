module abs_diff_i3072_o1536(a,b,r);
input [1535:0] a,b;
output [1535:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
