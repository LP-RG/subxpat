module abs_diff_i768_o384(a,b,r);
input [383:0] a,b;
output [383:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
