module abs_diff_i36864_o18432(a,b,r);
input [18431:0] a,b;
output [18431:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
