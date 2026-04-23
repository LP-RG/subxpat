module abs_diff_i4608_o2304(a,b,r);
input [2303:0] a,b;
output [2303:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
