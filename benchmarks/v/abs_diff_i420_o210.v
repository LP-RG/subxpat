module abs_diff_i420_o210(a,b,r);
input [209:0] a,b;
output [209:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
