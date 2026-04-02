module abs_diff_i412_o206(a,b,r);
input [205:0] a,b;
output [205:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
