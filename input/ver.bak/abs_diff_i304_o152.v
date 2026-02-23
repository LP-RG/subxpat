module abs_diff_i304_o152(a,b,r);
input [151:0] a,b;
output [151:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
