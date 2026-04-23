module abs_diff_i120_o60(a,b,r);
input [59:0] a,b;
output [59:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
