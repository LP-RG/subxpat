module abs_diff_i2304_o1152(a,b,r);
input [1151:0] a,b;
output [1151:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
