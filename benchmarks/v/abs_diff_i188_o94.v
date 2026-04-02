module abs_diff_i188_o94(a,b,r);
input [93:0] a,b;
output [93:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
