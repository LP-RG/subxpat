module abs_diff_i44_o22(a,b,r);
input [21:0] a,b;
output [21:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
