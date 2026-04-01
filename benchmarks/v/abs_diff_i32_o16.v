module abs_diff_i32_o16(a,b,r);
input [15:0] a,b;
output [15:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
