module abs_diff_i440_o220(a,b,r);
input [219:0] a,b;
output [219:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
