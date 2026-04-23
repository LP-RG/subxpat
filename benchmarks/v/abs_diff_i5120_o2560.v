module abs_diff_i5120_o2560(a,b,r);
input [2559:0] a,b;
output [2559:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
