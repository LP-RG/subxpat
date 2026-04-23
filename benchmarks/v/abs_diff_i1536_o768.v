module abs_diff_i1536_o768(a,b,r);
input [767:0] a,b;
output [767:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
