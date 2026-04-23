module abs_diff_i256_o128(a,b,r);
input [127:0] a,b;
output [127:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
