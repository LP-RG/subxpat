module abs_diff_i664_o332(a,b,r);
input [331:0] a,b;
output [331:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
