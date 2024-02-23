module abs_diff_i40_o20(a,b,r);
input [19:0] a,b;
output [19:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
