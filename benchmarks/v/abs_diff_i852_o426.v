module abs_diff_i852_o426(a,b,r);
input [425:0] a,b;
output [425:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
