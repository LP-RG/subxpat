module abs_diff_i2048_o1024(a,b,r);
input [1023:0] a,b;
output [1023:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
