module abs_diff_i548_o274(a,b,r);
input [273:0] a,b;
output [273:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
