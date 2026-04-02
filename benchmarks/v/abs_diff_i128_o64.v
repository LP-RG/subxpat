module abs_diff_i128_o64(a,b,r);
input [63:0] a,b;
output [63:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
