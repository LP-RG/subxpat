module abs_diff_i468_o234(a,b,r);
input [233:0] a,b;
output [233:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
