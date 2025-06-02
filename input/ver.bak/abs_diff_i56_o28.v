module abs_diff_i56_o28(a,b,r);
input [27:0] a,b;
output [27:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
