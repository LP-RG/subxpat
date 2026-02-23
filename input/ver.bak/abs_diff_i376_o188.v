module abs_diff_i376_o188(a,b,r);
input [187:0] a,b;
output [187:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
