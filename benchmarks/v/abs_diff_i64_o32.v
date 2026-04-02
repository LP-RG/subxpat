module abs_diff_i64_o32(a,b,r);
input [31:0] a,b;
output [31:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
