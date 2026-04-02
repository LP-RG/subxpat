module abs_diff_i892_o446(a,b,r);
input [445:0] a,b;
output [445:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
