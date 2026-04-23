module abs_diff_i18_o9(a,b,r);
input [8:0] a,b;
output [8:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
