module abs_diff_i752_o376(a,b,r);
input [375:0] a,b;
output [375:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
