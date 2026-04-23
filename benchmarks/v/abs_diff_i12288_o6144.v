module abs_diff_i12288_o6144(a,b,r);
input [6143:0] a,b;
output [6143:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
