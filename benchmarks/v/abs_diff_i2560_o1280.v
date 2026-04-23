module abs_diff_i2560_o1280(a,b,r);
input [1279:0] a,b;
output [1279:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
