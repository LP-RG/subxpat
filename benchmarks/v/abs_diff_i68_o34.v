module abs_diff_i68_o34(a,b,r);
input [33:0] a,b;
output [33:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
