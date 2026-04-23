module abs_diff_i14_o7(a,b,r);
input [6:0] a,b;
output [6:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
