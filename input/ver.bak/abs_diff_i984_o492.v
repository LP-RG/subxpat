module abs_diff_i984_o492(a,b,r);
input [491:0] a,b;
output [491:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
