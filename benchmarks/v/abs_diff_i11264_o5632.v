module abs_diff_i11264_o5632(a,b,r);
input [5631:0] a,b;
output [5631:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
