module abs_diff_i864_o432(a,b,r);
input [431:0] a,b;
output [431:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
