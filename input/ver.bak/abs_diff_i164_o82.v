module abs_diff_i164_o82(a,b,r);
input [81:0] a,b;
output [81:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
