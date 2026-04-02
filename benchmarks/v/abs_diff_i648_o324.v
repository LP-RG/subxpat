module abs_diff_i648_o324(a,b,r);
input [323:0] a,b;
output [323:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
