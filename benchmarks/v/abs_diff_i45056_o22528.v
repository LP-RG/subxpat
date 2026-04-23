module abs_diff_i45056_o22528(a,b,r);
input [22527:0] a,b;
output [22527:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
