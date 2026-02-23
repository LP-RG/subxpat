module abs_diff_i72_o36(a,b,r);
input [35:0] a,b;
output [35:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
