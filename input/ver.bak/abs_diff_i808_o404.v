module abs_diff_i808_o404(a,b,r);
input [403:0] a,b;
output [403:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
