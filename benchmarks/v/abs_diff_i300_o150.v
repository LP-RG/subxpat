module abs_diff_i300_o150(a,b,r);
input [149:0] a,b;
output [149:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
