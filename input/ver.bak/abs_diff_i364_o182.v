module abs_diff_i364_o182(a,b,r);
input [181:0] a,b;
output [181:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
