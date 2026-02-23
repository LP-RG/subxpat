module abs_diff_i972_o486(a,b,r);
input [485:0] a,b;
output [485:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
