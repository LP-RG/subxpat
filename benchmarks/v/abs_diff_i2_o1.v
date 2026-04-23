module abs_diff_i2_o1(a,b,r);
input [0:0] a,b;
output [0:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
