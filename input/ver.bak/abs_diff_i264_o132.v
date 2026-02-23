module abs_diff_i264_o132(a,b,r);
input [131:0] a,b;
output [131:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
