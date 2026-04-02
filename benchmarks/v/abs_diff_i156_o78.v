module abs_diff_i156_o78(a,b,r);
input [77:0] a,b;
output [77:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
