module abs_diff_i24_o12(a,b,r);
input [11:0] a,b;
output [11:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
