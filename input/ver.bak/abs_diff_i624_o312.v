module abs_diff_i624_o312(a,b,r);
input [311:0] a,b;
output [311:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
