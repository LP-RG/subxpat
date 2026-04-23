module abs_diff_i1152_o576(a,b,r);
input [575:0] a,b;
output [575:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
