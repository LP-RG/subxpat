module abs_diff_i948_o474(a,b,r);
input [473:0] a,b;
output [473:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
