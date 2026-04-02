module abs_diff_i520_o260(a,b,r);
input [259:0] a,b;
output [259:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
