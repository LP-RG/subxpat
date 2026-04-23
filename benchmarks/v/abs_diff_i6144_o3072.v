module abs_diff_i6144_o3072(a,b,r);
input [3071:0] a,b;
output [3071:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
