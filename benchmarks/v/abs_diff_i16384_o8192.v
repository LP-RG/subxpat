module abs_diff_i16384_o8192(a,b,r);
input [8191:0] a,b;
output [8191:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
