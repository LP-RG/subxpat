module abs_diff_i3584_o1792(a,b,r);
input [1791:0] a,b;
output [1791:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
