module abs_diff_i3328_o1664(a,b,r);
input [1663:0] a,b;
output [1663:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
