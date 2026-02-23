module abs_diff_i444_o222(a,b,r);
input [221:0] a,b;
output [221:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
