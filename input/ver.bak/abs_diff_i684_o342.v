module abs_diff_i684_o342(a,b,r);
input [341:0] a,b;
output [341:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
