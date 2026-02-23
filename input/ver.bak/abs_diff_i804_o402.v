module abs_diff_i804_o402(a,b,r);
input [401:0] a,b;
output [401:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
