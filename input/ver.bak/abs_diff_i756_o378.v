module abs_diff_i756_o378(a,b,r);
input [377:0] a,b;
output [377:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
