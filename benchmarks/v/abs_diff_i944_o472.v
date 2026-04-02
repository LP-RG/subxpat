module abs_diff_i944_o472(a,b,r);
input [471:0] a,b;
output [471:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
