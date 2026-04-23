module abs_diff_i22528_o11264(a,b,r);
input [11263:0] a,b;
output [11263:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
