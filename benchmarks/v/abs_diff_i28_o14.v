module abs_diff_i28_o14(a,b,r);
input [13:0] a,b;
output [13:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
