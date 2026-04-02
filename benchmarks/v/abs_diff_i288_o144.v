module abs_diff_i288_o144(a,b,r);
input [143:0] a,b;
output [143:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
